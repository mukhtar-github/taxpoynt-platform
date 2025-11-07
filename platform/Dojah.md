• We can use Dojah to pre-fill the “Company” step so users just review/confirm instead of retyping. A flow that works well:

- Step 1 – Account: collect email/password as you already do. Kick off the onboarding session and send the verification email.
- Step 2 – Verify: let the user enter the email OTP/token. On success, immediately ask for the TIN or RC number (if you haven’t already). As soon as they submit the identifier, call Dojah in the background; show a short-loading state (“Fetching company profile…”). If Dojah responds with a match, persist the payload on the onboarding session (we already store metadata on the domain object) and route to step 3.
- Step 3 – Company: render the profile with the data we just pulled—registered name, address, directors, RC/TIN, status, etc.—pre-filled. Label them as “Verified from Dojah” with a little badge so users know it came from an authoritative source. Allow edits on any field (in case the data is outdated or they want to add supplementary info). On submit we merge any edits back into CompanyProfile.

• Edge cases:
- If Dojah doesn’t find a match (or the call times out), show a friendly fallback: “We couldn’t fetch your company automatically—please fill in the details manually.” Keep a Retry button if they mistyped the identifier.
- Some fields might be optional; use the response to disable/enable sections (e.g., show a warning if status isn’t “Active”).

• On the back end:
- Extend SubmitKYCCommand to stash the Dojah response (we’re already storing metadata on CompanyProfile).
- Make sure the onboarding checklist marks “Company Info” as complete once the user confirms the pre-filled form.

This gives users a slick experience—verify, review, done, while keeping manual entry as a fallback.
