# Authentication Specification

## Purpose
Token-based authentication for the NITA Webapp REST API. All API endpoints
require a valid token obtained from the token endpoint.

## Requirements

### Requirement: Token Issuance
The system SHALL issue an authentication token when valid credentials are
submitted to POST /api/v1/auth/token/.

#### Scenario: Valid credentials
- GIVEN a Django superuser with username and password
- WHEN POST /api/v1/auth/token/ is called with those credentials as JSON
- THEN a 200 response is returned containing a `token` string

#### Scenario: Invalid credentials
- GIVEN an incorrect username or password
- WHEN POST /api/v1/auth/token/ is called
- THEN a 400 response is returned and no token is issued

### Requirement: Token Authentication on All Endpoints
The system SHALL reject requests to any /api/v1/ endpoint that do not include a
valid Authorization header.

#### Scenario: Missing token
- GIVEN no Authorization header is present
- WHEN any GET /api/v1/ endpoint is called
- THEN a 401 or 403 response is returned

#### Scenario: Valid token accepted
- GIVEN a valid token is included as `Authorization: Token <token>`
- WHEN any /api/v1/ endpoint is called
- THEN the request is processed normally

### Requirement: Session Authentication
The system SHALL also accept Django session cookies for browser-based access to
the API browsable interface.

#### Scenario: Session cookie accepted
- GIVEN a user is logged in via the Django session mechanism
- WHEN an API endpoint is accessed from the same browser session
- THEN the request is authenticated and returns data

### Requirement: Default Credentials
The system SHALL ship with default credentials of username `vagrant` and
password `vagrant123` for use in development and initial setup.

#### Scenario: Default login works after install
- GIVEN NITA has just been installed
- WHEN POST /api/v1/auth/token/ is called with vagrant / vagrant123
- THEN a token is returned
