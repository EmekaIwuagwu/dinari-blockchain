#!/bin/bash
# Debug Oracle Cloud CLI Connection

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Debugging Oracle Cloud CLI Connection${NC}"

# Test 1: Check if OCI CLI is installed
echo -e "\n${BLUE}1. Checking OCI CLI installation...${NC}"
if command -v oci &> /dev/null; then
    echo -e "${GREEN}✅ OCI CLI is installed${NC}"
    oci --version
else
    echo -e "${RED}❌ OCI CLI not found${NC}"
    exit 1
fi

# Test 2: Check config file
echo -e "\n${BLUE}2. Checking OCI config file...${NC}"
if [ -f ~/.oci/config ]; then
    echo -e "${GREEN}✅ Config file exists${NC}"
    echo "Config contents:"
    cat ~/.oci/config
else
    echo -e "${RED}❌ Config file missing at ~/.oci/config${NC}"
    echo -e "${YELLOW}You need to configure OCI CLI first!${NC}"
    exit 1
fi

# Test 3: Check private key
echo -e "\n${BLUE}3. Checking private key...${NC}"
if [ -f ~/.oci/oci_api_key.pem ]; then
    echo -e "${GREEN}✅ Private key exists${NC}"
elif [ -f ~/.oci/private_key.pem ]; then
    echo -e "${GREEN}✅ Private key exists (private_key.pem)${NC}"
else
    echo -e "${RED}❌ Private key missing${NC}"
    ls -la ~/.oci/
fi

# Test 4: Test basic connectivity
echo -e "\n${BLUE}4. Testing OCI API connectivity...${NC}"
echo "Trying: oci iam region list"
if timeout 30 oci iam region list > /dev/null 2>&1; then
    echo -e "${GREEN}✅ OCI API connection successful${NC}"
    oci iam region list
else
    echo -e "${RED}❌ OCI API connection failed or timed out${NC}"
    echo "This might be due to:"
    echo "- Incorrect credentials"
    echo "- Network timeout"
    echo "- Wrong tenancy/user configuration"
fi

# Test 5: Test specific compartment
echo -e "\n${BLUE}5. Testing compartment access...${NC}"
COMPARTMENT_ID="ocid1.tenancy.oc1..aaaaaaaa7gystzyxk5pxolz4bk4e2datu4flt57evnfymzzt3onmttubcopq"
echo "Trying: oci iam availability-domain list --compartment-id ${COMPARTMENT_ID}"
if timeout 30 oci iam availability-domain list --compartment-id ${COMPARTMENT_ID} > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Compartment access successful${NC}"
    oci iam availability-domain list --compartment-id ${COMPARTMENT_ID}
else
    echo -e "${RED}❌ Compartment access failed${NC}"
fi

echo -e "\n${BLUE}🎯 Diagnosis complete!${NC}"