# Resetting an Instance Admin's password

For an admin who has forgotten their password when the instance has **no SMTP**, so Plane's
"Forgot password" email cannot be sent. It runs through the "Data operations (manual)" workflow on
the dev-ai runner, so nobody needs shell access.

## Steps

1. In GitHub: **Settings → Secrets and variables → Actions → New repository secret**.
   Name `ADMIN_NEW_PASSWORD`, value the new password: at least 12 characters and not easy to guess
   (Plane's own strength check applies).
2. **Actions → Data operations (manual) → Run workflow**: part `reset-admin-password`, `email` the
   admin's address, **leave "apply" unticked**. This is a dry run: it checks the account and that the
   secret is an acceptable password, and writes nothing.
3. Run it again with "apply" ticked. A database backup is taken first, like every real run.
4. Sign in to Plane with the new password.
5. **Delete the `ADMIN_NEW_PASSWORD` secret**, and change the password from Plane's own
   Profile → Security settings, so the value that was in the secret is not the one you keep.

## Safeguards

* The password is only ever the secret: not an input, not on a command line, not printed. This
  repository's logs are public, and neither the password nor the email appears in them.
* It acts only on an existing, **active Instance Admin or superuser**. Any other account is refused,
  so it cannot be used to take over an ordinary member.
* The command is `python manage.py set_instance_admin_password --email <email> [--dry-run]`, with the
  password in the `VJ_NEW_PASSWORD` environment variable. It can also be run directly where the API
  runs, for anyone who does have a shell.

## If the account is not an Instance Admin

The run fails with "not an Instance Admin". Make it one first with the `instance-admin` part of the
same workflow (the account must have signed in once), then reset the password.
