---
name: social-post
description: Generate a social media post for any platform (LinkedIn, Facebook, Instagram, Twitter) and route through approval. Specify platform and topic as arguments. Use when the CEO requests social media content for any channel.
user-invocable: true
argument-hint: <platform> <topic or key message>
---

# Social Media Post Generator — WEBXES Tech

Generate a platform-appropriate social media post and route it through the approval workflow.

## Supported Platforms
- **linkedin** — Professional, long-form (150-300 words)
- **facebook** — Conversational, medium-form (100-200 words)
- **instagram** — Visual-first, caption-style (50-150 words), auto-generates image card
- **twitter** — Punchy, max 280 characters

## Workflow

1. **Parse arguments** — First word is platform, rest is topic. Default to `linkedin` if no platform specified.
2. **Read Company Handbook** (`Company_Handbook.md`) — refresh brand voice rules (Section 2.4)
3. **Generate post content** tailored to the platform's style and character limits
4. **Write approval file** to `/Pending_Approval/social_media/`
5. **Do NOT publish** — all AI-generated posts require APPROVE level per handbook

## Post Guidelines

- **Tone:** Knowledgeable, approachable, results-oriented (per handbook Section 2.4)
- **No emojis** in client-facing content (per handbook Section 2.1)
- **Never** engage in controversial topics (per handbook Section 2.4)
- **Hashtags:** 3-5 relevant hashtags (LinkedIn, Facebook, Instagram). None for Twitter.

## Platform-Specific Rules

| Platform   | Length       | Style                        |
|------------|-------------|------------------------------|
| LinkedIn   | 150-300 words | Hook → Value → CTA         |
| Facebook   | 100-200 words | Conversational, relatable   |
| Instagram  | 50-150 words  | Caption with line breaks    |
| Twitter    | ≤280 chars    | Punchy, one key insight     |

## Approval File Format

Write to `/Pending_Approval/social_media/POST_<Platform>_<DATE>.md`:

```markdown
---
type: social_media
action_type: social_media
platform: <linkedin|facebook|instagram|twitter>
generated: <ISO timestamp>
expires: <24 hours from now, ISO timestamp>
status: pending_approval
---

## <Platform> Post — Pending Approval

**Platform:** <platform>
**Topic:** <topic from arguments>
**Generated:** <date and time>
**Expires:** <24 hours from generation>

---

<full post content here>

---

## Instructions for CEO
- **To approve:** Move this file to `/Approved/social_media/`
- **To reject:** Move this file to `/Rejected/social_media/`
- **To edit:** Modify the post content above before approving
```

## After Writing

Confirm to the user:
- The approval file path
- Which platform the post targets
- That it will be published once moved to `/Approved/social_media/`
- That it expires in 24 hours if not acted upon
