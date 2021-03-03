# stop script on error
set -e

# Check to see if root CA file exists, download if not
if [ ! -f ./certificates/root-CA.crt ]; then
  printf "\nDownloading AWS IoT Root CA certificate from AWS...\n"
  curl https://www.amazontrust.com/repository/AmazonRootCA1.pem > /certificates/root-CA.crt
fi


printf "\nRunning client application...\n"
python client.py
