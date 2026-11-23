# Optional KartScope gameplay videos

The frontend patch does **not** include recordings. To enable the on-page players, copy your own captured gameplay footage to this folder using these exact names:

- `good_race.mp4` — used by the Good race card on `/dashboard`.
- `bad_race.mp4` — used by the Bad race card on `/dashboard`.
- `rainbow-preview.mp4` — muted looping clip used on `/upload` (you can copy a short part of the good race here).

The app displays a designed fallback if any file is missing. Use clips from your own recordings. Keep large video files untracked in Git unless your team deliberately decides how to distribute them. These MP4 paths are ignored by `.gitignore`.

Use short compressed clips for the preview to reduce loading times. Both the video players and all analysis routes still work without the clips.
