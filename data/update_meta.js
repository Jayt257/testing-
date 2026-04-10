const fs = require('fs');

const langs = ['en', 'es', 'fr', 'de', 'ar', 'zh', 'pt', 'ko'];
const basePath = 'c:/Users/jayta/OneDrive/Desktop/Mtech/Sem-2/GenAI/_Project/GenAI/learnwise/data/languages/hi';

for (const lang of langs) {
  const metaPath = `${basePath}/${lang}/meta.json`;
  if (fs.existsSync(metaPath)) {
    let data = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
    if (data.months && data.months.length > 0) {
      data.months[0].weeks = [
        {
          "week": 1,
          "globalWeek": 1,
          "title": "Basics & Greetings",
          "activities": [
            { "id": 1, "type": "lesson", "file": "month-1/week-1-lesson.json", "xp": 30 }
          ]
        }
      ];
      data.status = "active";
      data._status = "1 lesson implemented";
      fs.writeFileSync(metaPath, JSON.stringify(data, null, 2));
      console.log(`Updated meta.json for hi -> ${lang}`);
    }
  } else {
      console.log(`meta.json not found for hi -> ${lang}`);
  }
}
