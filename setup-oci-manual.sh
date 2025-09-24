#!/bin/bash
# Manual OCI CLI Setup Script

echo "🔧 Setting up Oracle Cloud CLI manually..."

# Create .oci directory
mkdir -p ~/.oci
chmod 700 ~/.oci

# Create config file
cat > ~/.oci/config << 'EOF'
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaahlpnzh7au6257k3oo6l3dxmqurs2m4u7ukc4iud6pqd4mxf4ys4q
fingerprint=ef:0e:8a:db:85:fb:fb:11:d3:eb:5d:e4:20:33:90:26
tenancy=ocid1.tenancy.oc1..aaaaaaaa7gystzyxk5pxolz4bk4e2datu4flt57evnfymzzt3onmttubcopq
region=eu-marseille-1
key_file=~/.oci/oci_api_key.pem
EOF

# Create private key file
cat > ~/.oci/oci_api_key.pem << 'EOF'
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDsnL4Aqpg5oHRQ
JbZ5PaZP42T/kP2m9SiDqZSLKB9GeW4zxEbBQ8+pK5UcbQj5KIAqtvKSjJX3MWuI
9hqoUzoIiAVd2FHB//u4L2QojxmByHXt7j7+Ejxztqizu/NOTYNUpouLxFr15GYj
MkIdTc/FRsIQN5mC8MHYEnqbTEhKoTdOs7ssNeByFWct//sk9bB8J4GxeyDL1Y0A
1x/SG9S7cJmujBHW0wbgyjwSEX46VVLLFMYI9YFNhzXvlP93usySWDtlzrTiISzq
yJeTWoIkeyyvD2tJQwxmQ4CQTLy/niJnG5Z7uz8C/jb3llQJiAdgsclCt3KQnuV4
fYrikIUdAgMBAAECggEAKhor7vdsFdj4yWgkg4dWSCHYz2bv050NA/yRW3+crRAf
bWOwCWS1F0+TfVbjgV5VDAS4vh34817eWSUdkjUY/vqhJdU/mwsfMeNw6YypB8Bx
R5Ccsd3x1s86Tp0TiqvdQhtOemTKoLVu/TVMsWUuotZX4sXZ8YRAod+L5IVa2bhl
gOeH2zkdErxtQKlO5u3dRIfreexSSZPZPcmnt9PEkQL+lH8g55qdDMIsVCOjHRA5
g3QF4IJQGWuSdFl8Z1zPgjHD+xz7o43uHBcsNtIRxBCVzBJq9kDWAVNZsB8jE+Gu
bdsq0SgE/8d3MgwDerhjY3jQM/0tKP8JLSNZRddWywKBgQD7cvIUoGsteQT6uxx2
5CNwGSfZWiwS6hgH/5NTtKXev++dkPUDhbHS6Q94heIRAEm5VgrtXo+sZZooRDkH
nqj+1g91LPv5UpPTVK0RLoaIaELQ1A7e8Qcyheo9Fso4zRY56wf2/TtG2PY1ceXN
VrFwB8rTPuN9eaL2YarBygOYUwKBgQDw5Q14E+5ucLSpfzmJUazOm9oKq4uYRegt
aUGoJWs9Rz0pCq8vGRWZAdsTffXzAygMXTJ5K9N14Q0S8JDphvZSZRJWyxgQePYg
QboBQzkvnWm44xZCMjHE6HlsfmBMRnX87sQKhx6u4UJeECPPPyl7U++8+bt/uj27
poNwnKL+zwKBgErY6F5jcgPTJjxMPijVuAbCNi5ovP3UWNropL4h483ubDEG2Sf3
P/t8DHLfx28wGsHkbtRBdZrnk3+w7xjpjXxt06QZg9evUPlzFyEqLDmmb10iAlsy
e+X6HsOYaRGHWrpaz8AhmOd55a/6+2CoEaE7cJB5A9ZxwqR8ZgvRSkipAoGAWsDQ
TDamEvFe/qQxluwwQD4y7OYn1xwvFjybQa+nMRTPk9C0ove+TUCHulYv/Hdp9Q5/
X2sFZVl9xW7gCTqRPgVZ3VzyGfKYNxrL6oHa33dcRw02a4Xhfh9e72LFALdi6AFD
1fuFsbineix2cTOIey/qF7W1z67oZvOafShlt70CgYEAtc6yAkUfs3AULkGod90/
79Q9LvgmCZeM/AfBaMIXGSdq8gKhTAVkuvQXfy4es83QHf5xpg1N+lJ7ODQi8CBa
INZ2w/kNnwgAGdGKAXFAE/YW/c6RA/J3mn984SEKN7zZDcuceK00E+d/CPCQYYDy
JLRu449y7KzJm10y0BhgH8E=
-----END PRIVATE KEY-----
EOF

# Set proper permissions
chmod 600 ~/.oci/config
chmod 600 ~/.oci/oci_api_key.pem

echo "✅ OCI CLI configuration complete!"
echo "📍 Config file: ~/.oci/config"
echo "🔑 Private key: ~/.oci/oci_api_key.pem"

# Test the configuration
echo "🧪 Testing connection..."
if oci iam region list > /dev/null 2>&1; then
    echo "✅ OCI CLI connection successful!"
else
    echo "❌ OCI CLI connection failed. Check your credentials."
fi