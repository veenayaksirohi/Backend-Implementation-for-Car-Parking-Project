# Backend-Implementation-for-Car-Parking-Project   
  
  

"""
# 📄 Test Plan: Flask Parking System API

---

## 1. Test Plan Overview

This document defines the test strategy, scenarios, cases, and data used for testing the Parking System Flask API using Pytest. It aims to validate user authentication, parking operations, and protected route behavior. 

---

## 2. Objectives

- Validate successful and unsuccessful user registration and login.
- Ensure parking lot CRUD operations function correctly.
- Test JWT-protected endpoints for valid/invalid tokens.
- Confirm slot allocation and deallocation behavior.
- Validate user update constraints.

---

## 3. Test Environment

| Component              | Details                             |
|------------------------|-------------------------------------|
| Framework              | Flask                               |
| Test Framework         | Pytest                              |
| DB                     | PostgreSQL (`parking_test`)         |
| Authentication         | JWT-based                           |
| OS                     | Linux / macOS / Windows             |
| Python Version         | 3.9+                                |
| Key Env Variables      | `JWT_SECRET_KEY`, DB credentials    |

---

## 4. Test Data

### 4.1 Initial DB Entries (created in fixture):

| Entity         | Data                                             |
|----------------|--------------------------------------------------|
| User           | `test@example.com / password`                    |
| Parking Lot    | ID: `1`, Name: `Test Parking`                    |
| Floor          | ID: `1`, Name: `Ground Floor`                    |
| Row            | ID: `1`, Name: `A`                               |
| Slot           | ID: `1`, Name: `A1`, Status: `0` (available)     |

### 4.2 Dynamic Users

- New user: `new@example.com`
- Duplicate user: `test@example.com`
- Secondary user for conflict: `second@example.com`

---

## 5. Test Scenarios and Test Cases

| TC ID | Test Case Description                            | Endpoint                    | Method  | Expected Result                            | Data / Token Required |
|-------|---------------------------------------------------|-----------------------------|---------|---------------------------------------------|------------------------|
| TC001 | Home page accessible                              | `/`                         | GET     | 200 + "Car Parking System API"              | No                     |
| TC002 | Register new user                                 | `/register`                | POST    | 201 + user_id + success message             | Yes                    |
| TC003 | Register user with missing fields                 | `/register`                | POST    | 400 + "Missing fields"                      | Partial data           |
| TC004 | Register duplicate user                           | `/register`                | POST    | 400 + "already registered"                  | Existing email         |
| TC005 | Login with correct email                          | `/login`                   | POST    | 200 + JWT token                             | Valid credentials      |
| TC006 | Login with phone number                           | `/login`                   | POST    | 200 + JWT token                             | Valid phone number     |
| TC007 | Login with wrong password                         | `/login`                   | POST    | 401 + "Invalid credentials"                 | Invalid credentials    |
| TC008 | Login with missing credentials                    | `/login`                   | POST    | 400 + "Missing credentials"                 | Empty JSON             |
| TC009 | Get parking lot details with token                | `/parkinglots_details`     | GET     | 200 + Parking lot data                      | Valid JWT              |
| TC010 | Get parking lot details without token             | `/parkinglots_details`     | GET     | 401 + "Authentication token is required"    | No                     |
| TC011 | Get hierarchical parking structure                | `/parking_lot_structure`   | GET     | 200 + floor/row/slot info                   | Valid JWT              |
| TC012 | Get list of users                                 | `/users`                   | GET     | 200 + user data                             | Valid JWT              |
| TC013 | Park car with basic data                          | `/park_car`                | POST    | 201 + assigned slot                         | Valid JWT              |
| TC014 | Park car missing fields                           | `/park_car`                | POST    | 400 + "Missing required fields"             | Valid JWT              |
| TC015 | Park car in specific slot                         | `/park_car`                | POST    | 201 + assigned slot                         | Valid JWT + slot IDs   |
| TC016 | Remove parked car with valid ticket               | `/remove_car_by_ticket`    | DELETE  | 200 + slot freed                            | Valid JWT + ticket     |
| TC017 | Remove car with invalid ticket                    | `/remove_car_by_ticket`    | DELETE  | 404                                         | Invalid ticket         |
| TC018 | Update user successfully                          | `/users/1`                 | PUT     | 200 + updated name                          | Valid JWT              |
| TC019 | Update another user's profile                     | `/users/2`                 | PUT     | 403 + "only update your own profile"        | Valid JWT              |
| TC020 | Update user with invalid ID                       | `/users/999`               | PUT     | 404                                         | Invalid user ID        |
| TC021 | Update user to duplicate email                    | `/users/1`                 | PUT     | 400 + "already in use"                      | Valid JWT              |

---

## 6. Execution Notes

- Ensure DB is dropped and recreated for test isolation (handled in fixture).
- Use `get_auth_token(user_id=...)` to generate tokens in protected tests.
- Run tests via:

```bash
pytest test_app.py -v
```


# Test Report

*Report generated on 14-May-2025 at 16:30:49 by [pytest-md-report]*

[pytest-md-report]: https://pypi.org/project/pytest-md-report/

## Summary

21 tests ran in 6.95 seconds

- 21 passed
- 0 failed
- 0 skipped
- 0 xfailed
- 0 xpassed
- 0 errors

## Detailed Results

| Test Name                                 | Outcome | Details                                                                                     |
|-------------------------------------------|---------|---------------------------------------------------------------------------------------------|
| test_home_page                            | Passed  |                                                                                             |
| test_register_user_success                | Passed  | {'message': 'User registered successfully', 'user_id': 2}                                    |
| test_register_user_missing_fields         | Passed  |                                                                                             |
| test_register_user_duplicate_email        | Passed  |                                                                                             |
| test_login_success                        | Passed  |                                                                                             |
| test_login_phone_success                  | Passed  |                                                                                             |
| test_login_invalid_credentials            | Passed  |                                                                                             |
| test_login_missing_credentials            | Passed  |                                                                                             |
| test_get_parkinglots_details_with_token   | Passed  | [{'address': 'Test Address', 'city': 'Test City', 'landmark': 'Test Landmark', 'parking_name': 'Test Parking', 'parkinglot_id': 1}] |
| test_get_parkinglots_details_no_token     | Passed  |                                                                                             |
| test_parking_lot_structure_with_token     | Passed  |                                                                                             |
| test_get_users_with_token                 | Passed  |                                                                                             |
| test_park_car_success                     | Passed  | {'assigned_slot': {'floor_id': 1, 'row_id': 1, 'slot_id': 1}, 'message': 'Car parked successfully', 'ticket_id': 'TKT-1-1747218108'} |
| test_park_car_missing_fields              | Passed  |                                                                                             |
| test_park_car_specific_slot               | Passed  |                                                                                             |
| test_remove_car_success                   | Passed  |                                                                                             |
| test_remove_car_invalid_ticket            | Passed  |                                                                                             |
| test_update_user_success                  | Passed  |                                                                                             |
| test_update_user_not_own_profile          | Passed  |                                                                                             |
| test_update_user_invalid_id               | Passed  | b'{"error":"User not found"}\n'                                                              |
| test_update_user_duplicate_email          | Passed  |                                                                                             |



