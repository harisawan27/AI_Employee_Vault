---
name: linkedin-post
description: Generate a LinkedIn post for WEBXES Tech and route it through the approval workflow. Creates professional content aligned with brand voice, then writes an approval file to /Pending_Approval/social_media/. Use when the CEO requests a social media post or when marketing content is needed.
user-invocable: true
argument-hint: [topic or key message for the post]
---

# LinkedIn Post Generator — WEBXES Tech

Generate a professional LinkedIn post and route it through the approval workflow.

## Workflow

1. **Read Company Handbook** (`Company_Handbook.md`) — refresh brand voice rules (Section 2.4)
2. **Read Business Goals** (`Business_Goals.md`) if it exists — align post with current marketing goals
3. **Generate post content** based on `$ARGUMENTS` (topic/message provided by user)
4. **Write approval file** to `/Pending_Approval/social_media/`
5. **Do NOT publish** — all new AI-generated posts require APPROVE level per handbook

## Post Guidelines

- **Tone:** Knowledgeable, approachable, results-oriented (per handbook Section 2.4)
- **Length:** 150-300 words. Use short paragraphs with line breaks for readability
- **Structure:** Hook → Value → Call-to-action
- **Hashtags:** 3-5 relevant hashtags at the end
- **No emojis** in client-facing content (per handbook Section 2.1)
- **Never** engage in controversial topics (per handbook Section 2.4)

## Approval File Format

Write to `/Pending_Approval/social_media/POST_LinkedIn_<DATE>.md`:

```markdown
---
type: social_media
action_type: social_media
platform: linkedin
generated: <ISO timestamp>
expires: <24 hours from now, ISO timestamp>
status: pending_approval
---

## LinkedIn Post — Pending Approval

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
- That the post will be published once moved to `/Approved/social_media/`
- That it expires in 24 hours if not acted upon
