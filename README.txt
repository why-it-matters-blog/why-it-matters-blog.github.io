WHY IT MATTERS - DASHBOARD (kaise use karein)
=============================================

Ek baar ka setup
- Computer mein Python 3 hona chahiye (python.org se free). Kuch aur install nahi karna.

Dashboard kholna
- Windows : start-dashboard.bat par double-click
- Mac/Linux: start-dashboard.command par double-click
  (ya terminal mein:  python3 admin.py)
- Browser mein dashboard apne aap khul jayega (http://localhost:8000).
- Band karne ke liye black window band kar do ya Ctrl+C dabao.

Login
- Pehli baar dashboard khologe to "Create your login" page aayega. Apna username aur
  password banao (password kam se kam 8 characters). Ye yaad rakhna.
- Uske baad har baar login page aayega. Bina login ke dashboard, articles, images aur ZIP
  kuch nahi khulta.
- 5 baar galat password dalne par thodi der ke liye login ruk jata hai.
- Password badalna: Dashboard > Settings > Change password.
- Password bhool gaye? data/auth.json file delete kar do, phir dashboard dobara kholo aur
  naya login bana lo. (Articles ko kuch nahi hota.)
- Logout: dashboard ke upar "Logout" button.
- Dhyan rahe: dashboard sirf aapke computer par (localhost) chalta hai. Ise internet par
  mat chalana.

Naya article daalna
1. "+ New article" dabao.
2. Title, category, short description bharo, colour chuno.
3. Feature image upload karo.
4. Content blocks se heading / paragraph / list / image daalo.
   Image block se article ke beech mein kahin bhi image laga sakte ho.
5. Chaho to FAQ aur final takeaway bhi daalo.
6. "Save & update site" dabao. Site ki files apne aap ban/update ho jati hain.
   Draft chunoge to article site par nahi dikhega.

Pehle se likha article: "Paste article text" se paste karo, form apne aap fill ho jayega.

Site live karna
- Dashboard mein "Download site ZIP" dabao.
- Us ZIP ki sab files apni hosting par upload karo (purani files replace).
- Dashboard sirf aapke computer par chalta hai. Live site sirf simple HTML/CSS files hain,
  isliye koi database ya server ki zaroorat nahi.

Folders
- public/     -> asli website (yahi upload hota hai)
- data/       -> articles (har article ek .json file) aur settings
- dashboard/  -> dashboard ka design (upload nahi karna)
- templates/  -> site ke upar/neeche ka hissa (menu, footer)
- Backup lena ho to poora folder copy kar lo, khaaskar data/ aur public/.
