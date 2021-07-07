# Mario Kart Wii Tool-Assisted Speedrun Database
A one-stop shop to view all Nintendo track "Best Known Times" (BKTs) and current work-in-progress (WIPs) for Mario Kart Wii Tool-Assisted Speedruns. This repo also houses the Discord Bot that we use to interface with the repo from Discord.

## Bot Features Implemented
Input parameters within [ ] are optional.

`!bkt <track> [category] [laps]`
  - Retrieves the best-known time (BKT) for a (optional) given category and/or number of laps (3lap/flap)
  - Directly links to the .rkg file for this ghost
  - If no ghost file is uploaded, links to the YouTube encode
## Todo
- Implement Discord Bot to create commits based off of messages posted to #collab-rksys. Otherwise, post notification in #collab-rksys if a commit is manually created on GitHub (if possible)
  - If user uploads directly, do we have a lists of pre-approved users or do we maintain a moderation process?
- Create folder hierarchy and establish how to organize BKTs vs. WIPs, and how to handle categories.
  - UPDATE: Added example folder hierarchy.
- Determine whether the repo should be public or limited to private chat members who wish to view it
  - If public, the process of uploading or replacing files is moderated through pull requests, so there is no risk of trolls trying to destroy repo.
