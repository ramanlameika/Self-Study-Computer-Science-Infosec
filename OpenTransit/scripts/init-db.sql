-- Initialize per-service databases
CREATE DATABASE opentransit_auth;
CREATE DATABASE opentransit_ticketing;
CREATE DATABASE opentransit_fare;
CREATE DATABASE opentransit_agency;
CREATE DATABASE opentransit_payment;

GRANT ALL PRIVILEGES ON DATABASE opentransit_auth TO opentransit;
GRANT ALL PRIVILEGES ON DATABASE opentransit_ticketing TO opentransit;
GRANT ALL PRIVILEGES ON DATABASE opentransit_fare TO opentransit;
GRANT ALL PRIVILEGES ON DATABASE opentransit_agency TO opentransit;
GRANT ALL PRIVILEGES ON DATABASE opentransit_payment TO opentransit;
