## ADDED Requirements

### Requirement: Create User (Admin UI)
The admin `Users` screen SHALL provide a **New user** action that opens a dialog
collecting `username`, `email`, `role`, and an initial `password`, and submits it
to `POST /api/v1/users/`. On success the new user SHALL appear in the list. The
dialog SHALL offer a way to generate and copy the password client-side, and SHALL
surface `400` validation errors (duplicate username, weak password) inline. The
password SHALL only exist client-side for copying; it SHALL never be displayed
from a server response.

#### Scenario: Admin creates a user from the UI
- **GIVEN** a logged-in admin on `/users`
- **WHEN** they open **New user**, enter a username, email, role, and password, and submit
- **THEN** `POST /api/v1/users/` is sent and, on 201, the new user appears in the list

#### Scenario: Validation errors are shown in the dialog
- **GIVEN** the New user dialog is open
- **WHEN** submission returns a 400 (e.g. duplicate username or weak password)
- **THEN** the dialog stays open and shows the error next to the relevant field

### Requirement: Reset User Password (Admin UI)
Each row on the `Users` screen SHALL provide a **Reset password** action that
opens a dialog collecting a new `password` and submits it to
`POST /api/v1/users/{id}/set_password/`. The dialog SHALL offer generate/copy for
the password and SHALL surface `400` validation errors inline. On success it
SHALL confirm the reset. The password SHALL never be displayed from a server
response.

#### Scenario: Admin resets a user's password from the UI
- **GIVEN** a logged-in admin on `/users`
- **WHEN** they choose **Reset password** on a row, enter a new password, and submit
- **THEN** `POST /api/v1/users/{id}/set_password/` is sent and, on 200, a confirmation is shown

#### Scenario: Weak reset password is rejected in the dialog
- **GIVEN** the Reset password dialog is open
- **WHEN** submission returns a 400 for a weak password
- **THEN** the dialog stays open and shows the validation error
