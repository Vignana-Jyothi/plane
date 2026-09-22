# Member Directory Enhancements Specification

This specification documents the changes required to expand the ecosystem's **Member Directory** to support custom role names, role changes, and photo/avatar uploads.

---

## 1. Data Model Changes (Django Backend)

The `OrganizationMemberProfile` table will act as the source of truth for directory listings:

```python
# models/organization.py
class OrganizationMemberProfile(BaseModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=255, default="Member")  # Editable custom role name
    is_club_member = models.BooleanField(default=False)
    wing = models.ForeignKey(Wing, on_delete=models.SET_NULL, null=True, blank=True)
    # user.avatar is inherited from Plane's User table and holds the profile picture URL.
```

---

## 2. API Contract (PATCH /api/vj-startups/admin/members/<id>/)

To update a member's details, the admin panel calls the member detail endpoint.

### Request Payload:
```json
{
  "role": "Lead Innovation Engineer",
  "is_club_member": true,
  "wing": "4f9d0c27-393f-4e08-9df8-2c286d9a9cb2"
}
```

### Picture Upload Strategy:
Admins can upload profile images. On submit:
1. The frontend uploads the file to Plane's media storage using the stock `/api/assets/` endpoint (returning a `file_url`).
2. The frontend patches the user record with the new asset URL:
   ```json
   { "avatar": "http://minio-url/bucket/avatar.png" }
   ```

---

## 3. Frontend Component Design (apps/admin)

We will update the Wing details page and the members directories:

### Directory Table Additions:
- **Photo Column**: Renders the member's avatar image. Shows a placeholder circle with initials if no image is present.
- **Custom Role Column**: Inline edit option or click-to-edit input that triggers a PATCH request.

### Edit Member Modal:
An overlay offering:
1. **Photo Dropzone**: Drags and drops or clicks to select a JPG/PNG. Uses the `use-file-upload` hook.
2. **Role Name Input**: Text field to type custom roles (e.g. `President`, `Core Member`, `VNR Lead`).
3. **Wing Selector**: Dropdown listing active wings from `/api/vj-startups/admin/wings/`.
