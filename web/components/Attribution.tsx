// N-03/N-04: 青空文庫(底本・入力校正者)と地理院タイルの帰属を常時表示
export default function Attribution() {
  return (
    <footer className="attribution">
      地図タイル:{" "}
      <a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noreferrer">
        国土地理院
      </a>
      {" ｜ 本文: "}
      <a href="https://www.aozora.gr.jp/" target="_blank" rel="noreferrer">
        青空文庫
      </a>
      (PD・底本表記は各引用末尾)｜ 特徴量・整列データ: CC BY 4.0(yamato-gaze)
    </footer>
  );
}
