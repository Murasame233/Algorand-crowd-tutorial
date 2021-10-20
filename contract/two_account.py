import algosdk
private_a, address_a = algosdk.account.generate_account()
private_b, address_b = algosdk.account.generate_account()

print("A:\nprivate key: " + private_a + "\naddress: " + address_a);
print("B:\nprivate key: " + private_b + "\naddress: " + address_b);

print("faucet: https://bank.testnet.algorand.network/")
