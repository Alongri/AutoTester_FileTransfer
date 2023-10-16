dir
echo %1
echo %2

call conda env update -n myenv --file file_transfer_env.yml --prune
call conda activate myenv
echo %CONDA_DEFAULT_ENV%

set new_version="%1"
set workdir="%2"
python %workdir%\version_change.py %new_version% %workdir%

cd scripts
pyinstaller --onedir --noconsole --icon icon.ico Autotester_FileTransfer.py 
xcopy /E /I "images" "dist\Autotester_FileTransfer\images"
powershell Compress-Archive -Path "dist\Autotester_FileTransfer" -DestinationPath "Autotester_FileTransfer_%1.zip"
call conda deactivate