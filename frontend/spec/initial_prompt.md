RAG Application Blueprint Creation Prompt
Create a comprehensive blueprint and visual design specification for a modern RAG (Retrieval-Augmented Generation) demo application with the following requirements:
Technology Stack

Frontend: React with TypeScript
Styling: Tailwind CSS
Authentication: Supabase Auth with Google OAuth option
Backend: Node.js with Express
Database: Supabase
State Management: Redux

Application Structure

1. Authentication Flow

Initial Login Screen

Clean, modern login interface
Supabase authentication integration
Google OAuth button
Email/password option
Responsive design for mobile and desktop

2. Main Dashboard Layout
   Create a single-page application with three main sections accessible via navigation:
   Chat Interface

Real-time chat interface for RAG interactions
Message history display
Input field with send functionality
Loading states for AI responses
Message timestamps
Clear conversation option

Documents Management

Knowledge base document viewer
Document upload functionality
Document preview/summary cards
Search and filter capabilities
Document categories or tags
Delete/edit document options

Settings Panel

User profile management
Account settings
Authentication preferences
Application preferences
Data management options

Visual Design Theme
Color Scheme: "Neon Dark"

Primary: Deep purple/violet tones (#1a0b2e, #16213e, #0f3460)
Accent: Electric yellow/neon highlights (#ffff00, #f1c40f, #e74c3c)
Background: Rich dark gradients and solid blacks
Text: Light grays and whites with yellow accents for important elements
Interactive Elements: Glowing yellow borders, hover effects with neon glow

Design Characteristics

Dark theme with subtle gradients
Neon glow effects on interactive elements
Clean, minimal interface with cyberpunk aesthetics
Smooth animations and transitions
Glass-morphism elements where appropriate
Sharp, modern typography

Technical Requirements
Component Architecture

Modular React components with TypeScript interfaces
Redux store for global state management
Custom hooks for authentication and data fetching
Responsive grid layouts using Tailwind CSS
Error boundaries and loading states

Key Features to Design

Responsive Navigation - Sidebar or top nav with smooth transitions
Real-time Chat - WebSocket integration planning
Document Upload - Drag-and-drop interface with progress indicators
Search Functionality - Global search across documents and chat history
User Feedback - Toast notifications, loading spinners, error states

Deliverables Requested

Wireframe Layouts for each main screen
Component Hierarchy diagram
Color Palette with exact hex codes
Typography Scale recommendations
Interactive States documentation (hover, active, disabled)
Responsive Breakpoints strategy
Animation Guidelines for transitions and micro-interactions
Accessibility Considerations for the dark theme

Design Constraints

Mobile-first responsive design
Fast loading times with optimized assets
Keyboard navigation support
Screen reader compatibility
Cross-browser compatibility (Chrome, Firefox, Safari, Edge)

Please create a detailed blueprint that includes visual mockups, component specifications, and implementation guidelines that align with modern web development best practices and the specified neon-dark aesthetic.



API Endpoint to agent

http://localhost:8001/api/pydantic-agent

SUPABASE INFO
No need to ask me to configure supabase use what is below



NEXT_PUBLIC_SUPABASE_URL=https://hlnolmntioyrkllpbpbg.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY=sb_publishable_lWwCpV_69qt6I1vKDc1GSA_HHkcadJk
