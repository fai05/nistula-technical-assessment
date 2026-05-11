-- ============================================================
-- PostgreSQL Schema
-- ============================================================

-- TABLE RELATIONSHIPS
-- guests: Stores one profile per guest.
-- guest_channel_identities: Maps one guest to multiple channels such as WhatsApp, Airbnb or Instagram.
-- properties: Stores Nistula property details.
-- reservations: Stores booking details and links each reservation to a guest and property.
-- conversations: Groups related messages between Nistula and a guest.
-- messages: Stores every inbound and outbound message along with AI classification, confidence score, drafted reply, final reply and action.

-- Enables UUID generation using gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ------------------------------------------------------------
-- ENUM TYPES
-- ------------------------------------------------------------

CREATE TYPE channel_source AS ENUM (
    'whatsapp',
    'booking_com',
    'airbnb',
    'instagram',
    'direct'
);

CREATE TYPE message_direction AS ENUM (
    'inbound',
    'outbound'
);

CREATE TYPE query_type AS ENUM (
    'pre_sales_availability',
    'pre_sales_pricing',
    'post_sales_checkin',
    'special_request',
    'complaint',
    'general_enquiry'
);

CREATE TYPE ai_action AS ENUM (
    'auto_send',
    'agent_review',
    'escalate'
);

CREATE TYPE message_handling_status AS ENUM (
    'received',
    'ai_drafted',
    'agent_edited',
    'auto_sent',
    'agent_sent',
    'escalated'
);

CREATE TYPE reservation_status AS ENUM (
    'enquiry',
    'confirmed',
    'cancelled',
    'completed'
);

-- ------------------------------------------------------------
-- GUESTS
-- One guest profile can be linked to multiple channels.
-- ------------------------------------------------------------

CREATE TABLE guests (
    guest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(30),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------
-- GUEST CHANNEL IDENTITIES
-- Stores channel-specific identifiers for the same guest.
-- Example: one guest may contact through WhatsApp and Airbnb.
-- ------------------------------------------------------------

CREATE TABLE guest_channel_identities (
    identity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_id UUID NOT NULL REFERENCES guests(guest_id) ON DELETE CASCADE,
    source channel_source NOT NULL,
    external_guest_id VARCHAR(255),
    channel_display_name VARCHAR(150),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_guest_channel_identity
        UNIQUE (source, external_guest_id)
);

-- ------------------------------------------------------------
-- PROPERTIES
-- Stores Nistula properties such as Villa B1.
-- ------------------------------------------------------------

CREATE TABLE properties (
    property_id VARCHAR(100) PRIMARY KEY,
    property_name VARCHAR(150) NOT NULL,
    location VARCHAR(255),
    max_guests INT,
    base_rate_per_night NUMERIC(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------
-- RESERVATIONS
-- A reservation belongs to one guest and one property.
-- Conversations can optionally be linked to a reservation.
-- ------------------------------------------------------------

CREATE TABLE reservations (
    reservation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_ref VARCHAR(100) UNIQUE NOT NULL,
    guest_id UUID NOT NULL REFERENCES guests(guest_id) ON DELETE CASCADE,
    property_id VARCHAR(100) NOT NULL REFERENCES properties(property_id),
    check_in_date DATE,
    check_out_date DATE,
    number_of_guests INT,
    reservation_status reservation_status DEFAULT 'enquiry',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------
-- CONVERSATIONS
-- A conversation groups related messages from a guest.
-- It is linked to a guest and optionally to a reservation.
-- ------------------------------------------------------------

CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_id UUID NOT NULL REFERENCES guests(guest_id) ON DELETE CASCADE,
    reservation_id UUID REFERENCES reservations(reservation_id) ON DELETE SET NULL,
    source channel_source NOT NULL,
    subject VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------
-- MESSAGES
-- Stores all inbound and outbound messages across all channels.
-- AI classification, confidence, drafted replies and final action are stored here for inbound messages.
-- ------------------------------------------------------------

CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    source channel_source NOT NULL,
    direction message_direction NOT NULL,

    message_text TEXT NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Used only for inbound messages after classification
    query_type query_type,
    ai_confidence_score NUMERIC(4, 3)
        CHECK (ai_confidence_score >= 0 AND ai_confidence_score <= 1),

    -- Stores the AI-generated draft before it is sent or edited
    ai_drafted_reply TEXT,

    -- Stores the final reply if edited or sent by an agent
    final_reply TEXT,

    -- Tracks whether the message was AI drafted, edited by agent, auto-sent, or escalated
    handling_status message_handling_status DEFAULT 'received',

    -- Stores the backend action decision from Part 1
    action ai_action,

    -- Optional fields
    agent_id VARCHAR(100),
    agent_notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------
-- INDEXES
-- These make common lookups faster.
-- ------------------------------------------------------------

CREATE INDEX idx_guests_email ON guests(email);
CREATE INDEX idx_guests_phone ON guests(phone);

CREATE INDEX idx_reservations_booking_ref ON reservations(booking_ref);
CREATE INDEX idx_reservations_guest_id ON reservations(guest_id);

CREATE INDEX idx_conversations_guest_id ON conversations(guest_id);
CREATE INDEX idx_conversations_reservation_id ON conversations(reservation_id);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_query_type ON messages(query_type);
CREATE INDEX idx_messages_handling_status ON messages(handling_status);
CREATE INDEX idx_messages_received_at ON messages(received_at);


/*DATABASE DESIGN EXPLANATION
I designed the schema around a unified messaging model where all guest messages from WhatsApp, Booking.com, Airbnb, Instagram and direct channels are stored in a single messages table. This avoids creating separate tables for each channel and makes it easier to search, analyse and process messages consistently.

The guests table stores the main guest profile, while guest_channel_identities stores channel-specific identifiers. This is important because the same guest may contact Nistula through multiple channels. For example, a guest may first enquire through Instagram and later continue the conversation through WhatsApp.

The conversations table links guests to reservations. A conversation can be connected to a reservation when a booking reference exists, but it can also exist without a confirmed reservation. This supports both pre-sales enquiries and post-booking communication.

The messages table stores both inbound and outbound messages. It includes fields for query type, AI confidence score, AI drafted reply, final reply, handling status and action. This allows the system to track whether a message was only drafted by AI, edited by an agent, auto-sent or escalated for manual handling.
*/


/*HARDEST DESIGN DECISION
The hardest design decision was deciding where to store the AI-generated reply and the final agent-handled reply.

Initially, I considered creating a separate table only for AI outputs because in a larger production system there may be multiple AI drafts, retries, edits or version history for the same message.

However, for this assessment, I kept the AI draft, final reply, confidence score, query type, handling status and action inside the messages table. I chose this because these fields are directly connected to the inbound guest message. Keeping them in one table makes the schema easier to understand and query for the current scope.

For example, if an agent wants to review a message, they can see the original guest message, AI draft, confidence score, final action and handling status from the same table. In a future production version, I would separate AI attempts and agent edits into a message versioning table so every draft, edit and decision can be tracked historically.
*/