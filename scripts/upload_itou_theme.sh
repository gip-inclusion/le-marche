#!/bin/bash

# This shell script will import the last theme version from
# https://github.com/betagouv/itou-theme

echo "Running the Upload Itou theme"

cd $APP_HOME

# Folder where the theme will be temporary stocked
tmpFolder="$APP_HOME/tmp"
tmpFolderDistribSources="$tmpFolder/dist"

# local folder where the source will be updated
localFolderTheme="$APP_HOME/lemarche/static/vendor/theme-inclusion"

repository="https://github.com/betagouv/itou-theme"

echo "localFolderTheme"
echo $localFolderTheme


# create temporary folder
mkdir -p $tmpFolder

copyAndReplaceFolderTheme() {
    local folderToReplace=$1
    cp -TRv "$tmpFolderDistribSources/$folderToReplace/" "$localFolderTheme/$folderToReplace/"
}

# clone the repository in temp folder
git clone $repository $tmpFolder

# copy and replace all files in those folders
copyAndReplaceFolderTheme fonts
copyAndReplaceFolderTheme images
copyAndReplaceFolderTheme javascripts
copyAndReplaceFolderTheme stylesheets

rm -rf $tmpFolder
