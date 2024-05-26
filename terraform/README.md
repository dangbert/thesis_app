# Infrastucture Management
> This folder defines/documents the cloud infrastructure needs for deploying the ezfeedback site.

In summary the site is deployed on a single AWS EC2 instance (manually deployed with docker compose).  Auth0 is used as a service for user management and proving the Google social login flow.  AWS SES is used as an email sending provider (e.g. allowing students to receive email alerts when their assignment feedback is ready).

Note: before committing in this folder run `terraform fmt -recursive`

### Auth0 and EC2 Setup

1. Login/signup to https://auth0.com and create a new tenant.
    * Choose the region of deployment that matches where the site itself is (or will be) deployed.

2. Create application "Terraform Auth0 Provider":
    * Go to "Applications" and click "Create Application", name it "Terraform Auth0 Provider", chose the "Machine to Machine" application type, and authorize all permissions to the "Auth0 Management API" [as shown here](https://images.ctfassets.net/23aumh6u8s0i/2YGSCKRVyLL9BLo0HsauE8/8aadf0888bbb6f15491552321e6de9a3/m2m-scope-selection).
    * Open the "Settings" tab within the application and copy the Domain, Client ID, and Client Secret values (for use below).

3. Manual Tenant Steps
    * Under `Applications > Database` delete "Username-Password-Authentication" (as we'll just support Google login)
    * Under "Applications" feel free to delete "Default App"
    * Also under "Authentication > Social" feel free to delete the "google-oauth2" connection as we'll create it later with terraform (otherwise you'll have to `terraform import module.auth0_tenant.auth0_connection.google`) later.

4. Follow the [Google Social Connection installation steps here](https://marketplace.auth0.com/integrations/google-social-connection), creating your project on https://console.cloud.google.com
  * In your project under `Credentials > OAuth2.0 Client IDs`, be sure to add your "https://CHANGE_ME.eu.auth0.com/login/callback" (substituting in your Auth0 domain name) under "Authorized redirect URIs.

5. Instantiate an instance of the `modules/auth0-tenant` module, placing the credentials copied in step 2 in a terraform.tfvars file.
    * see `instances/DEV` for an example that manages just an auth0 tenant (no server).  As a starting point you can also `cp terraform.tfvars.sample terraform.tfvars`
    * see `instances/PRD` for a complete example which also creates an EC2 server for deploying the production site!
    * And just run `terraform init && terraform apply` in one of these folders (or a copy based on them) to start managing your tenant with Terraform :) and to deploy a server which can be manually setup via ssh for hosting the site.

6. DNS Setup:
  * add an "A Record" pointing to the server's IP (visible in `terraform output`) on your domain provider's website.
  * ssh into the server, and run `bash ~/setup.sh -i` to install certbot and create your SSL certificates.

7. Then follow the production instructions in [../docker/README.md](../docker/README.md) to launch the site!

### Common Infrastructure

The [./common](./common) folder defines cloud resources (e.g. SES email templates) needed by all deployment environments.

After running `terraform init && terraform apply` in `common/`, be sure to then manually verify your domain on [AWS SES](https://console.aws.amazon.com/ses/home#/homepage) (and "Request production access" to leave the sandbox) before you'll be able to freely send emails.  Be sure to do this in the same region selected in [common/main.tf](./common/main.tf).
