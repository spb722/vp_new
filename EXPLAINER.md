# How the VP Resolver Works — A Simple Explanation
uvicorn api:app --host 0.0.0.0 --port 8000

## What does this system do?

Imagine you have a business rule written in plain English, like:

> *"Customers who made more than 3 recharges in the last 30 days"*

This system automatically converts that plain English sentence into a precise, machine-readable rule that can be applied to a database. Think of it like translating human language into a language computers can act on — without anyone having to write code manually.

---

## The Flow, Step by Step

### Step 1 — Understand the Request (`parse_request`)

The system first **reads and understands** what you typed.

It breaks the sentence into smaller pieces — for example:
- What are we measuring? → *recharges*
- What is the condition? → *more than 3*
- Over what time period? → *last 30 days*

> Think of this like a person reading a sentence and highlighting the important parts.

---

### Step 2 — Find a Matching Template (`select_seed`)

The system has a **library of templates** (we call them "seeds"). Each template is a pre-approved pattern for a type of rule.

It looks through the library and tries to find the template that best fits your request.

Three things can happen here:

| Outcome | What it means |
|---|---|
| **Match found** | A good template was found. Move forward. |
| **No match found** | No template fits. The system cannot proceed. |
| **Ambiguous client** | Two equally good templates exist but for different telecom clients. The system pauses and asks: *"Which client is this for — Airtel or Omantel?"* |

> Think of this like finding the right form to fill out. If there's no form for your situation, we can't proceed yet.

---

### Step 3 — Look Up the Exact Data Columns (`resolve_columns`)

Once a template is found, the system needs to know **exactly which database columns** to use.

For example, "recharge count" needs to be mapped to the actual column name in the database (e.g., `RECHARGE_COUNT_30D`).

It calls an internal service to confirm these column names exist and are valid.

> Think of this like looking up the correct filing cabinet drawer before filling in the form.

---

### Step 4 — Fill in the Template (`render_condition`)

Now the system **fills in the template** with the actual values — the column names, the time period, the thresholds — to produce the final rule.

If something goes wrong here (e.g., a value doesn't fit the template correctly), the system tries again — up to **2 times** — and each time it sends a correction hint back to the AI so it can fix its understanding of the request.

> Think of this like filling out a form with the right answers. If you make a mistake, you get two chances to correct it.

---

### Step 5 — Check the Output (`validate_output`)

Before declaring success, the system does a **final quality check**:

- Is the output non-empty?
- Are all placeholders properly filled in?
- Was a valid data column found?
- Was a template selected?

If all checks pass → **Success.**
If any check fails → **Failure.**

> Think of this like a supervisor reviewing the completed form before it's submitted.

---

### When Something Goes Wrong (`stop_failure`)

If the system fails at any step, it stops and clearly reports **why** it failed — so a human can investigate and fix the issue.

---

## What Happens When No Template is Found?

Sometimes the system cannot find a matching template for a new type of rule. This is expected — the library of templates grows over time.

Here is what you can do when this happens:

### 1. Provide the Training Data

Give the system two things:
- The **plain English sentence** (your input)
- The **correct machine-readable rule** (the expected output, called a `PARENT_CONDITION`)

### 2. A New Template is Created

The system automatically reverse-engineers the rule you provided and creates a new template (seed) from it. This new template is saved to the library.

### 3. It Works for Similar Rules Going Forward

From that point on, whenever someone types a similar request, the system will find the new template and handle it correctly — without any human intervention.

> Think of this like teaching the system a new form. Once the form exists, everyone can use it.

---

## Visual Summary

```
You type a sentence
        |
        v
  Understand it  ──(if retry needed, fix and try again)──┐
        |                                                  |
        v                                                  |
  Find a template                                         |
    |         |                                           |
    |      Ask which client?                              |
    |                                                     |
    v                                                     |
  Look up columns                                         |
        |                                                  |
        v                                                  |
  Fill in the template  ──(error? retry with hint) ───────┘
        |
        v
  Final quality check
        |
   Pass      Fail
    |           |
  Done      Report error
```

---

## In One Sentence

> The system reads what you type, finds the best matching rule template, fills it in with the right data, checks it, and gives you the final machine-readable rule — and if no template exists yet, you can teach it one.