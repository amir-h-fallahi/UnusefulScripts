# Challenge
While testing ESC1 (Template allows SAN) against ADCS I got an "Object SID mismatch" error. This was probably due to "Strong Certificate Mapping Enforcement" [KB5014754](https://support.microsoft.com/en-us/topic/kb5014754-certificate-based-authentication-changes-on-windows-domain-controllers-ad2c23b0-15d8-4340-a468-4d4f3b188f16).

The SID needs to match the target account identified through the certificate's SAN mapping.

So you have to provide a SID that corresponds to the target account (in tools like Certipy).

I quickly searched the Internet but couldn't find how to obtain a user's SID. (NXC has a fantastic --get-sid feature but it retrieves the Domain SID).

# Solution
I utilized ldapsearch to get objectSid (A binary value that specifies the SID) using a UPN and then converted it to the standard SID string format using a handy Python script.

# References
- https://www.thehacker.recipes/ad/movement/adcs/certificate-templates#weak-and-strong-mapping

# Proof of Concept

```bash
ldapsearch -LLL -x \
  -H ldap://<ad-ldap-address> \
  -D "user@domain.local" \
  -w "user" \
  -b "DC=domain,DC=local" \
  "(userPrincipalName=target_user@domain.local)" \                           
  distinguishedName sAMAccountName userPrincipalName objectSid
```

<img width="1191" height="412" alt="image" src="https://github.com/user-attachments/assets/f7f9da37-3ca6-413c-b7ba-e3fbe57c9fcb" />

