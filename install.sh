#!/bin/sh
# Builds the extension into a .vsix and installs it into VS Code.
#
# A .vsix is just a zip holding extension/, an OPC content-types file and a
# vsixmanifest, so this needs nothing but python3, zip and the `code` CLI -
# no vsce, no npm.
set -eu

cd "$(dirname "$0")"
ROOT=$(pwd)
BUILD="$ROOT/build"

VERSION=$(python3 -c 'import json;print(json.load(open("package.json"))["version"])')
NAME=$(python3 -c 'import json;print(json.load(open("package.json"))["name"])')
VSIX="$ROOT/$NAME-$VERSION.vsix"

echo "==> checking the manifest"
python3 - <<'PY'
import json, os, sys

m = json.load(open("package.json"))

# VS Code writes __metadata into the manifest of an INSTALLED extension. Finding it
# here means package.json was copied back out of ~/.vscode/extensions - i.e. a build
# artifact overwrote the source. Building from it would ship VS Code's bookkeeping
# and silently drop whatever the source manifest had gained since.
if "__metadata" in m:
    sys.exit(
        "ERROR: package.json contains __metadata, which VS Code only writes into\n"
        "       installed copies. This file came back out of ~/.vscode/extensions\n"
        "       and is a build artifact, not the source.\n\n"
        "       Recover it with:  git checkout package.json\n"
        "       The repo builds INTO the extensions folder, never the other way round.")

# The icon is easy to lose this way, and a missing one only shows up as a grey
# placeholder on the Marketplace, so fail loudly instead.
icon = m.get("icon")
if not icon:
    sys.exit('ERROR: package.json declares no "icon"; expected "icon.png".')
if not os.path.exists(icon):
    sys.exit("ERROR: package.json points at %s, which does not exist." % icon)
PY

echo "==> regenerating grammar and language configuration"
python3 tools/gen_grammar.py

echo "==> staging"
rm -rf "$BUILD"
mkdir -p "$BUILD/extension"
for f in package.json README.md icon.png language-configuration.json syntaxes snippets; do
  cp -R "$f" "$BUILD/extension/"
done
cp LICENSE "$BUILD/extension/LICENSE.txt"   # OPC wants a known file extension

python3 - "$BUILD" <<'PY'
import json, sys, xml.sax.saxutils as x

build = sys.argv[1]
p = json.load(open("package.json"))
esc = x.escape
tags = ",".join(p.get("keywords", []))
# The VS Code Marketplace wants a plain comma-separated string here. The nested
# <Category> form is the Visual Studio (not VS Code) manifest style and is rejected
# on upload with "The category '...' is not available in language 'en-us'".
cats = ",".join(p.get("categories", []))

open(build + "/extension.vsixmanifest", "w").write(f'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Language="en-US" Id="{esc(p['name'])}" Version="{esc(p['version'])}" Publisher="{esc(p['publisher'])}" />
    <DisplayName>{esc(p['displayName'])}</DisplayName>
    <Description xml:space="preserve">{esc(p['description'])}</Description>
    <Tags>{esc(tags)}</Tags>
    <Categories>{esc(cats)}</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{esc(p['engines']['vscode'])}" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="ui,workspace,web" />
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true" />
  </Assets>
</PackageManifest>
''')

open(build + "/[Content_Types].xml", "w").write(
    '<?xml version="1.0" encoding="utf-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension=".json" ContentType="application/json"/>'
    '<Default Extension=".vsixmanifest" ContentType="text/xml"/>'
    '<Default Extension=".md" ContentType="text/markdown"/>'
    '<Default Extension=".txt" ContentType="text/plain"/>'
    '<Default Extension=".py" ContentType="text/plain"/>'
    "</Types>\n")
PY

echo "==> packing $VSIX"
rm -f "$VSIX"
(cd "$BUILD" && zip -r -q -X "$VSIX" '[Content_Types].xml' extension.vsixmanifest extension)
rm -rf "$BUILD"

echo "==> installing"
code --install-extension "$VSIX" --force

echo
echo "Installed. Reload the VS Code window (Developer: Reload Window) to pick it up."
