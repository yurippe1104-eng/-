// 使い方: node make.js <お店> <仕入れ値> [相場] [商品写真のパス] [出力ファイル]
// 例:     node make.js ハードオフ 880 4800 photo.jpg out.png
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const [store = 'ハードオフ', price = '880', souba = '', photo = '', out] = process.argv.slice(2);
  const q = new URLSearchParams({ store, price });
  if (souba && souba !== '-') q.set('souba', souba);
  if (photo && photo !== '-') {
    const buf = fs.readFileSync(photo);
    const ext = path.extname(photo).slice(1).toLowerCase().replace('jpg', 'jpeg');
    q.set('photo', `data:image/${ext};base64,${buf.toString('base64')}`);
  }
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(__dirname, 'template.html') + '?' + q.toString());
  await page.waitForSelector('body[data-ready="1"]');
  const file = out || `${store}_${price}円.png`;
  await page.screenshot({ path: file });
  await browser.close();
  console.log(file);
})();
