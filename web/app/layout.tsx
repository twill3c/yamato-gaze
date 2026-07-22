import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "大和路の三面鏡 | yamato-gaze",
  description:
    "和辻哲郎『古寺巡礼』・亀井勝一郎『大和古寺風物誌』・堀辰雄『大和路・信濃路』を、奈良の寺院・仏像ごとに整列して読み比べる計量文体の地図。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
