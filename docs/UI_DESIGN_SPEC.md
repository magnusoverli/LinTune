# LinTune UI Design Specification

**Design Language:** Microsoft Fluent Design System (Intune Portal inspired)  
**Framework:** PyQt6 with custom QSS stylesheets

---

## Design Principles

### 1. Consistency with Microsoft Intune Portal
Users familiar with the Intune Portal should feel immediately at home. The interface mimics Microsoft's enterprise management aesthetic.

### 2. Clarity and Trust
System-level configuration requires user trust. Clear, professional design with transparent operations.

### 3. Progressive Disclosure
Show simple options by default, reveal advanced options when needed.

### 4. Responsive Feedback
Every action should have immediate visual feedback (progress, status changes, confirmations).

---

## Color Palette

### Primary Colors (Microsoft Fluent)
```python
COLORS = {
    # Primary
    'primary': '#0078D4',           # Microsoft Blue
    'primary_hover': '#106EBE',     # Darker blue
    'primary_pressed': '#005A9E',   # Even darker
    
    # Status Colors
    'success': '#107C10',           # Green
    'warning': '#FFB900',           # Gold/Yellow
    'error': '#E81123',             # Red
    'info': '#0078D4',              # Blue
    
    # Neutrals
    'background': '#F3F2F1',        # Light gray background
    'surface': '#FFFFFF',           # White cards/panels
    'surface_hover': '#F9F9F9',     # Subtle hover
    
    # Text
    'text_primary': '#323130',      # Dark gray
    'text_secondary': '#605E5C',    # Medium gray
    'text_disabled': '#A19F9D',     # Light gray
    'text_on_primary': '#FFFFFF',   # White on blue
    
    # Borders
    'border': '#EDEBE9',            # Very light gray
    'border_focus': '#0078D4',      # Blue when focused
    
    # Shadows (for elevation)
    'shadow_sm': 'rgba(0, 0, 0, 0.1)',
    'shadow_md': 'rgba(0, 0, 0, 0.15)',
    'shadow_lg': 'rgba(0, 0, 0, 0.2)',
}
```

---

## Typography

### Font Stack
```css
font-family: 
    "Segoe UI",           /* Windows */
    -apple-system,        /* macOS/iOS */
    "Ubuntu",             /* Ubuntu */
    "Cantarell",          /* GNOME */
    "Noto Sans",          /* Fallback */
    sans-serif;
```

### Font Sizes
```python
TYPOGRAPHY = {
    'heading_1': '28px',      # Page titles
    'heading_2': '20px',      # Section headers
    'heading_3': '16px',      # Card titles
    'body': '14px',           # Regular text
    'caption': '12px',        # Helper text, labels
    'button': '14px',         # Button text
}

FONT_WEIGHTS = {
    'light': 300,
    'regular': 400,
    'semibold': 600,
    'bold': 700,
}
```

---

## Spacing System

Based on 8px grid:

```python
SPACING = {
    'xs': '4px',    # Tight spacing
    'sm': '8px',    # Small gap
    'md': '16px',   # Standard gap
    'lg': '24px',   # Section spacing
    'xl': '32px',   # Major section spacing
    'xxl': '48px',  # Page-level spacing
}
```

---

## Components

### 1. Cards

**Elevation Levels:**
```css
/* Level 1 - Default cards */
background: #FFFFFF;
border: 1px solid #EDEBE9;
border-radius: 4px;
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
padding: 24px;

/* Level 2 - Hover state */
box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);

/* Level 3 - Active/Important */
box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
```

**Card Variants:**

```python
# Status Card
┌─────────────────────────┐
│  Status                 │
│  ───────────────────    │
│  ✓ Connected            │
│  ○ Not enrolled         │
│                         │
│  Domain: company.com    │
└─────────────────────────┘

# Action Card
┌─────────────────────────┐
│  Get started            │
│  ───────────────────    │
│  Configure device for   │
│  EntraID and Intune.    │
│                         │
│  [Begin setup]          │
└─────────────────────────┘

# Info Card (with icon)
┌─────────────────────────┐
│  ⓘ Prerequisites        │
│  ───────────────────    │
│  • GDM display manager  │
│  • Internet connection  │
│  • Sudo access          │
└─────────────────────────┘
```

---

### 2. Buttons

**Primary Button:**
```css
background: #0078D4;
color: #FFFFFF;
border: none;
border-radius: 4px;
padding: 8px 24px;
font-size: 14px;
font-weight: 600;

/* Hover */
background: #106EBE;

/* Pressed */
background: #005A9E;

/* Disabled */
background: #F3F2F1;
color: #A19F9D;
```

**Secondary Button:**
```css
background: transparent;
color: #0078D4;
border: 1px solid #0078D4;
border-radius: 4px;
padding: 8px 24px;

/* Hover */
background: #F3F2F1;
```

**Button Sizes:**
- Small: `padding: 4px 12px; font-size: 12px;`
- Default: `padding: 8px 24px; font-size: 14px;`
- Large: `padding: 12px 32px; font-size: 16px;`

---

### 3. Progress Indicators

**Linear Progress Bar:**
```
┌────────────────────────────────────┐
│ ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░   │  47%
└────────────────────────────────────┘
```

**Styling:**
```css
/* Track */
background: #EDEBE9;
height: 8px;
border-radius: 4px;

/* Fill */
background: linear-gradient(90deg, #0078D4 0%, #106EBE 100%);
border-radius: 4px;
```

**Circular Progress (Indeterminate):**
```
     ●●●○
    ●    ○
   ●      ○
    ●    ○
     ●●●○
```

---

### 4. Status Indicators

**Dot Indicators:**
```css
/* Success */
● color: #107C10;

/* Warning */
● color: #FFB900;

/* Error */
● color: #E81123;

/* Pending */
○ color: #A19F9D;
```

**Status Badge:**
```
┌───────────────┐
│ ● Compliant   │
└───────────────┘
```

```css
background: rgba(16, 124, 16, 0.1);  /* Light green */
color: #107C10;                      /* Dark green */
border-radius: 12px;
padding: 4px 12px;
font-size: 12px;
font-weight: 600;
```

---

### 5. Input Fields

**Text Input:**
```css
background: #FFFFFF;
border: 1px solid #EDEBE9;
border-radius: 4px;
padding: 8px 12px;
font-size: 14px;
color: #323130;

/* Focus */
border: 2px solid #0078D4;
outline: none;

/* Error */
border: 2px solid #E81123;

/* Disabled */
background: #F3F2F1;
color: #A19F9D;
```

**Label Style:**
```css
font-size: 12px;
font-weight: 600;
color: #323130;
margin-bottom: 4px;
```

**Helper Text:**
```css
font-size: 12px;
color: #605E5C;
margin-top: 4px;
```

---

### 6. Navigation Sidebar

**Layout:**
```
┌────┐
│ 🏠 │  Dashboard
│    │
│ 🖥 │  Devices
│    │
│ ⚙ │  Settings
│    │
│ 📄 │  Logs
│    │
│ ℹ │  About
│    │
│    │
│    │
└────┘
```

**Styling:**
```css
/* Sidebar */
background: #F3F2F1;
width: 64px;
border-right: 1px solid #EDEBE9;

/* Nav Item */
padding: 16px;
text-align: center;
cursor: pointer;

/* Hover */
background: rgba(0, 120, 212, 0.1);

/* Active */
background: #0078D4;
color: #FFFFFF;
border-left: 4px solid #005A9E;

/* Icon */
font-size: 24px;
margin-bottom: 4px;

/* Label */
font-size: 10px;
font-weight: 600;
text-transform: uppercase;
```

**Expanded State (on hover/click):**
```
┌────────────────────┐
│ 🏠  Dashboard      │
│                    │
│ 🖥  Devices        │
│                    │
│ ⚙  Settings       │
│                    │
│ 📄  Logs           │
│                    │
│ ℹ  About          │
└────────────────────┘
```

Width expands to 200px with smooth animation.

---

### 7. Step Progress Indicator

**Horizontal Stepper:**
```
●─────●─────○─────○─────○
Check  Prep  Build Config Done
```

**Styling:**
```css
/* Completed Step */
circle: #107C10;  /* Green */
line: #107C10;

/* Active Step */
circle: #0078D4;  /* Blue */
line: #EDEBE9;    /* Gray */

/* Future Step */
circle: #EDEBE9;  /* Gray outline */
line: #EDEBE9;
```

**Vertical Stepper (for sidebar):**
```
● Step 1: Check system
│  ✓ Compatible distro
│  ✓ GDM available
│
● Step 2: Install dependencies
│  → Installing rust...
│
○ Step 3: Build Himmelblau
○ Step 4: Configure
○ Step 5: Enroll
```

---

### 8. Toast Notifications

**Positions:** Top-right corner

**Success Toast:**
```
┌──────────────────────────────────┐
│ ✓  Installation successful       │
│    System is ready for login     │
└──────────────────────────────────┘
```

```css
background: #FFFFFF;
border-left: 4px solid #107C10;
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
padding: 16px;
border-radius: 4px;
```

**Variants:**
- Success: Green border (`#107C10`)
- Error: Red border (`#E81123`)
- Warning: Yellow border (`#FFB900`)
- Info: Blue border (`#0078D4`)

---

### 9. Modals/Dialogs

**Confirmation Dialog:**
```
┌───────────────────────────────────────────┐
│  Modify system configuration?             │
├───────────────────────────────────────────┤
│                                           │
│  This will modify:                        │
│  • PAM authentication (/etc/pam.d/)       │
│  • NSS configuration (/etc/nsswitch.conf) │
│                                           │
│  Backups will be created automatically.   │
│                                           │
│            [Cancel]  [Continue]           │
└───────────────────────────────────────────┘
```

**Styling:**
```css
/* Backdrop */
background: rgba(0, 0, 0, 0.4);

/* Dialog */
background: #FFFFFF;
border-radius: 8px;
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
max-width: 480px;
padding: 0;

/* Header */
padding: 24px 24px 16px 24px;
border-bottom: 1px solid #EDEBE9;
font-size: 20px;
font-weight: 600;

/* Content */
padding: 24px;

/* Footer */
padding: 16px 24px;
border-top: 1px solid #EDEBE9;
text-align: right;
```

---

### 10. Log Viewer

**Interface:**
```
┌────────────────────────────────────────────────┐
│ 📄 Logs                    [Clear] [Export]    │
├────────────────────────────────────────────────┤
│ 🔍 Filter: [___________]  [⚙ Level: All ▼]   │
├────────────────────────────────────────────────┤
│                                                │
│ 10:30:15 INFO  System check complete          │
│ 10:30:18 INFO  Installing dependencies        │
│ 10:31:42 WARN  GDM not found, installing...   │
│ 10:32:05 INFO  Building Himmelblau            │
│ 10:34:28 SUCCESS Build complete               │
│                                                │
│ ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯     │
└────────────────────────────────────────────────┘
```

**Log Entry Styling:**
```css
/* Container */
font-family: "Cascadia Code", "Fira Code", monospace;
font-size: 12px;
line-height: 1.6;
padding: 8px;

/* Level Colors */
.log-info { color: #323130; }
.log-success { color: #107C10; }
.log-warning { color: #FFB900; }
.log-error { color: #E81123; }
.log-debug { color: #605E5C; }

/* Timestamp */
color: #A19F9D;
font-weight: 600;
```

---

## Layout Grid

### Dashboard Layout
```
┌─────────────────────────────────────────────┐
│ 32px padding                                │
│  ┌───────────┐ ┌───────────┐ ┌──────────┐  │
│  │           │ │           │ │          │  │
│  │  Card 1   │ │  Card 2   │ │  Card 3  │  │
│  │           │ │           │ │          │  │
│  └───────────┘ └───────────┘ └──────────┘  │
│      24px gap between cards                 │
│  ┌─────────────────────────────────────┐   │
│  │                                     │   │
│  │         Wide Card                   │   │
│  │                                     │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

### Card Grid
- **Small cards:** 280px width
- **Medium cards:** 400px width
- **Large cards:** 100% width (with max-width)
- **Gap:** 24px between cards
- **Padding:** 32px from edges

---

## Animations

### Transition Timings
```css
/* Fast - Hover effects */
transition: all 0.15s ease-in-out;

/* Medium - Panel open/close */
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

/* Slow - Page transitions */
transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
```

### Common Animations

**Button Hover:**
```css
QPushButton:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}
```

**Card Reveal:**
```css
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

**Progress Pulse:**
```css
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}
```

---

## Icons

### Icon Set
Use **Fluent System Icons** (Microsoft's open-source icon set)  
https://github.com/microsoft/fluentui-system-icons

**Size Guide:**
- Toolbar icons: 20px
- Navigation icons: 24px
- Card header icons: 16px
- Inline icons: 14px

**Icon Colors:**
- Default: `#605E5C`
- Active: `#0078D4`
- Success: `#107C10`
- Warning: `#FFB900`
- Error: `#E81123`

---

## Responsive Behavior

### Window Sizes

**Minimum:** 960x600px  
**Recommended:** 1280x720px  
**Maximum:** Unlimited (scales with window)

### Breakpoints

- **Compact** (< 960px): Stack cards vertically, hide labels
- **Medium** (960-1280px): 2-column card layout
- **Wide** (> 1280px): 3-column card layout, full features

---

## Dark Mode (Future)

Reserve dark mode color scheme:

```python
DARK_COLORS = {
    'background': '#1E1E1E',
    'surface': '#2D2D2D',
    'text_primary': '#FFFFFF',
    'text_secondary': '#D0D0D0',
    'border': '#3D3D3D',
    # Keep same accent colors
}
```

---

## Accessibility

### WCAG 2.1 AA Compliance

**Color Contrast:**
- Text on background: 4.5:1 minimum
- Large text: 3:1 minimum
- Interactive elements: 3:1 minimum

**Keyboard Navigation:**
- All interactive elements must be keyboard-accessible
- Visible focus indicators
- Logical tab order

**Screen Reader Support:**
- ARIA labels on all controls
- Status announcements for async operations
- Descriptive button labels

---

## Implementation in PyQt6

### QSS Stylesheet Structure

```python
# Load stylesheets
def load_fluent_theme():
    with open('resources/styles/fluent.qss', 'r') as f:
        base_style = f.read()
    with open('resources/styles/colors.qss', 'r') as f:
        colors = f.read()
    return base_style + colors
```

### Sample QSS for Card Widget

```css
/* Card Widget */
QFrame[class="card"] {
    background-color: #FFFFFF;
    border: 1px solid #EDEBE9;
    border-radius: 4px;
    padding: 24px;
}

/* Primary Button */
QPushButton[class="primary"] {
    background-color: #0078D4;
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    padding: 8px 24px;
    font-size: 14px;
    font-weight: 600;
}

QPushButton[class="primary"]:hover {
    background-color: #106EBE;
}

QPushButton[class="primary"]:pressed {
    background-color: #005A9E;
}

QPushButton[class="primary"]:disabled {
    background-color: #F3F2F1;
    color: #A19F9D;
}
```

---

## Design Resources

### Fonts
- **Linux:** Install `fonts-segoe-ui` or use Ubuntu/Cantarell
- **Fallback:** System sans-serif

### Icons
- Download Fluent System Icons
- Convert to SVG for Qt
- Create icon theme

### Reference
- Microsoft Fluent Design: https://fluent2.microsoft.design/
- Intune Portal: https://intune.microsoft.com/ (for reference)
- Material for Qt: https://github.com/UN-GCPDS/qt-material (inspiration)

---

This design spec ensures LinTune looks professional, modern, and familiar to users who work with Microsoft enterprise tools.

