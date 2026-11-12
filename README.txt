WHY IT MATTERS - GITHUB PAGES + DASHBOARD
==========================================

Ye kaise kaam karta hai
- Website GitHub Pages par free host hoti hai.
- Dashboard bhi usi site par hai:  https://AAPKA-USERNAME.github.io/dashboard/
- Dashboard mein login GitHub token se hota hai. Token ke bina koi article add/edit/delete
  nahi kar sakta. Article save karte hi GitHub par save hota hai aur site 1-2 minute mein
  apne aap update ho jati hai. Database ya server nahi chahiye.

SETUP (sirf ek baar)
1. GitHub repo mein purani saari files hata do (ya naya repo banao: username.github.io).
2. Is ZIP ki SAARI files/folders repo ke root mein upload karo, jisme ".github" folder bhi hai.
   (Agar ".github" folder upload nahi hua: Add file > Create new file, naam likho
    .github/workflows/deploy.yml aur is ZIP wali deploy.yml ka text paste karo.)
3. Repo > Settings > Pages > "Build and deployment" > Source: "GitHub Actions".
4. Repo > Actions tab mein "Build and deploy site" chalegi. Green hone ka wait karo.
   Phir site khulegi: https://username.github.io/

TOKEN BANANA (dashboard login ke liye)
1. GitHub > Settings > Developer settings > Personal access tokens > Fine-grained tokens
   > Generate new token.
2. Repository access: "Only select repositories" > apna site repo.
3. Permissions > Repository permissions:
   - Contents: Read and write   (zaroori)
   - Actions: Read-only          (optional, site status dikhane ke liye)
4. Generate karke token copy karo (sirf ek baar dikhta hai) aur safe jagah rakho.
5. Dashboard kholo > username + repo ka naam + token daalo > Login.
   "Is device par yaad rakho" tick karoge to dobara token nahi daalna padega.
   Shared computer par tick mat karo, aur kaam ke baad Logout karo.

ARTICLE DAALNA
- "+ New article" > details, feature image, content blocks (heading, paragraph, lists, image),
  FAQ, takeaway > "Save & update site".
- Draft chunoge to article site par nahi dikhega.
- Pehle se likha article ho to "Paste article text" se paste karo.

SECURITY
- Token = password. Kisi ko mat do. Shak ho to GitHub mein token delete/revoke kar do.
- Token ki expiry date hoti hai. Expire hone par naya token banao aur dobara login karo.
- Repo public ho to articles ki files sabko dikhti hain (site ki tarah). Token kabhi repo
  mein mat daalna.

FOLDERS
- data/      articles (har article ek .json) aur settings
- public/    site ki design files, logo, images
- dashboard/ index.html = online dashboard (GitHub mode), local.html = computer wala purana
- admin.py   site banane wala script (GitHub Actions khud chalata hai)
- .github/   automatic build ka setup

OPTIONAL: computer par offline chalana
- start-dashboard.bat / start-dashboard.command (Python 3 chahiye). Ye local.html wala
  dashboard kholta hai, apne login ke saath.
