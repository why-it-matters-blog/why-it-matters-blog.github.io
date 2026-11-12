WHY IT MATTERS - WEBSITE + DASHBOARD (GitHub Pages)
====================================================

How it works
- The website is hosted for free on GitHub Pages.
- The dashboard lives on the same site: https://YOUR-USERNAME.github.io/dashboard/
- Logging in to the dashboard requires a GitHub access token. Without the token nobody can
  add, edit or delete articles. When you save an article it is stored on GitHub and the site
  updates automatically within 1-2 minutes. No database or server is needed.

ONE-TIME SETUP
1. In your GitHub repository, delete the old files (or create a new repository named
   username.github.io).
2. Upload ALL files and folders from this ZIP to the root of the repository, including the
   ".github" folder.
   (If the ".github" folder does not upload: Add file > Create new file, name it
    .github/workflows/deploy.yml and paste the contents of the deploy.yml file from this ZIP.)
3. Go to the repository > Settings > Pages > "Build and deployment" > Source: "GitHub Actions".
4. Open the repository's Actions tab. The "Build and deploy site" workflow will run. Wait for
   the green tick, then open https://username.github.io/

CREATING A TOKEN (needed to log in to the dashboard)
1. GitHub > Settings > Developer settings > Personal access tokens > Fine-grained tokens
   > Generate new token.
2. Repository access: "Only select repositories" > choose your site repository.
3. Permissions > Repository permissions:
   - Contents: Read and write   (required)
   - Actions: Read-only          (optional, lets the dashboard show the site status)
4. Generate the token, copy it (it is shown only once) and keep it somewhere safe.
5. Open the dashboard, enter your username, the repository name and the token, then click Login.
   Tick "Remember me on this device" to avoid typing the token again.
   Do not tick it on a shared computer, and always log out when you are done.

ADDING AN ARTICLE
- Click "+ New article", fill in the details, upload a feature image, add content blocks
  (heading, paragraph, lists, image), and optionally a FAQ and a final takeaway.
- Click "Save & update site". Choose "Draft" to keep an article off the site.
- If you already have the article written, use "Paste article text" to fill the form.

SECURITY
- The token works like a password. Never share it. If you think it has leaked, delete
  (revoke) it in GitHub and create a new one.
- Tokens expire. When it does, create a new one and log in again.
- If the repository is public, article files are visible to everyone, just like the site.
  Never put a token inside the repository.

FOLDERS
- data/       articles (one .json file each) and settings
- public/     site design files, logo and images
- dashboard/  index.html = online dashboard (GitHub mode), local.html = optional offline version
- admin.py    script that builds the site (GitHub Actions runs it automatically)
- .github/    automatic build setup

OPTIONAL: run the dashboard offline on your computer
- Double-click start-dashboard.bat (Windows) or start-dashboard.command (Mac/Linux).
  Python 3 is required. It opens the offline dashboard (local.html) with its own login.
