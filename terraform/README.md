# Infrastructure Management

## Auth0 Setup

1. Login/signup to https://auth0.com and create a new tenant.
    * Choose the region of deployment that matches where the site itself is (or will be) deployed.

2. Create application "Terraform Auth0 Provider":
    * Go to "Applications" and click "+ Create Application", name it "Terraform Auth0 Provider", chose the "Machine to Machine" application type, and authorize full permissions to the "Auth0 Management API" [as shown here](https://images.ctfassets.net/23aumh6u8s0i/2YGSCKRVyLL9BLo0HsauE8/8aadf0888bbb6f15491552321e6de9a3/m2m-scope-selection).
    * Open the "Settings" tab within the application and copy the Domain, Client ID, and Client Secret values (for use below).

3. Instantiate an instance of the `modules/auth0-tenant` modules, placing the credentials copied in step 2 in a terraform.tfvars file.
    * see `instances/DEV` as an example!  As a starting point you can also `cp terraform.tfvars.sample terraform.tfvars`
    * And just run `terraform init && terraform apply` to start managing your tenant with Terraform :)

4. Manual Tenant Steps
    * Under "Applications" delete "Default App"
    * Under `Authentication > Social` delete "google-auth2"