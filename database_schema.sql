CREATE TABLE clients (
    id BIGSERIAL PRIMARY KEY,
    client_code VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(150) NOT NULL,
    contact_name VARCHAR(150),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'France',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE drivers (
    id BIGSERIAL PRIMARY KEY,
    driver_code VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    license_number VARCHAR(100),
    current_city VARCHAR(100),
    status VARCHAR(30) NOT NULL DEFAULT 'Available',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE vehicles (
    id BIGSERIAL PRIMARY KEY,
    vehicle_code VARCHAR(50) UNIQUE NOT NULL,
    registration_number VARCHAR(50) UNIQUE NOT NULL,
    brand VARCHAR(100),
    model VARCHAR(100),
    vehicle_type VARCHAR(50),
    current_city VARCHAR(100),
    odometer_km INTEGER DEFAULT 0,
    fuel_type VARCHAR(50),
    status VARCHAR(30) NOT NULL DEFAULT 'Available',
    technical_inspection_date DATE,
    next_oil_change_km INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE missions (
    id BIGSERIAL PRIMARY KEY,
    reference VARCHAR(100) UNIQUE NOT NULL,

    client_id BIGINT REFERENCES clients(id),

    pickup_city VARCHAR(100) NOT NULL,
    delivery_city VARCHAR(100) NOT NULL,

    mission_date DATE NOT NULL,

    assigned_driver_id BIGINT REFERENCES drivers(id),
    assigned_vehicle_id BIGINT REFERENCES vehicles(id),

    distance_km INTEGER,

    status VARCHAR(30) NOT NULL DEFAULT 'New',

    source VARCHAR(50) DEFAULT 'Manual',
    source_email VARCHAR(255),

    notes TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE approvals (
    id BIGSERIAL PRIMARY KEY,

    mission_id BIGINT NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    driver_id BIGINT NOT NULL REFERENCES drivers(id),

    proposed_distance_km INTEGER,
    proposal_reason TEXT,

    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    rejection_reason TEXT,

    proposed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decided_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE email_imports (
    id BIGSERIAL PRIMARY KEY,

    message_id VARCHAR(255) UNIQUE NOT NULL,
    sender_email VARCHAR(255) NOT NULL,
    subject VARCHAR(255),

    mission_reference VARCHAR(100),

    status VARCHAR(30) NOT NULL DEFAULT 'Processed',
    error_message TEXT,

    received_at TIMESTAMP,
    processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_missions_status
ON missions(status);

CREATE INDEX idx_missions_date
ON missions(mission_date);

CREATE INDEX idx_missions_driver
ON missions(assigned_driver_id);

CREATE INDEX idx_approvals_mission
ON approvals(mission_id);

CREATE INDEX idx_approvals_driver
ON approvals(driver_id);

CREATE INDEX idx_approvals_status
ON approvals(status);

CREATE INDEX idx_email_imports_mission_reference
ON email_imports(mission_reference);
ALTER TABLE missions
ADD CONSTRAINT chk_missions_distance_nonnegative
CHECK (distance_km IS NULL OR distance_km >= 0);

ALTER TABLE approvals
ADD CONSTRAINT chk_approvals_distance_nonnegative
CHECK (proposed_distance_km IS NULL OR proposed_distance_km >= 0);

ALTER TABLE vehicles
ADD CONSTRAINT chk_vehicles_odometer_nonnegative
CHECK (odometer_km >= 0);

ALTER TABLE missions
ADD CONSTRAINT chk_missions_status
CHECK (status IN ('New', 'Pending', 'Assigned', 'Approved', 'Rejected', 'Completed', 'Cancelled'));

ALTER TABLE approvals
ADD CONSTRAINT chk_approvals_status
CHECK (status IN ('Pending', 'Approved', 'Rejected'));

ALTER TABLE drivers
ADD CONSTRAINT chk_drivers_status
CHECK (status IN ('Available', 'Assigned', 'Unavailable'));

ALTER TABLE vehicles
ADD CONSTRAINT chk_vehicles_status
CHECK (status IN ('Available', 'Assigned', 'Maintenance', 'Unavailable'));