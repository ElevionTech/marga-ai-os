"""Đa ngôn ngữ: dò ngôn ngữ, chốt ngôn ngữ, và các cổng chặn phải theo ngôn ngữ.

    python tests/run.py da_ngon_ngu

Bệnh thật đo được trên mã trước khi có tầng này (0.34.1):

    "tóm tắt đơn hàng"    -> bị chặn đúng, đi đường đầy đủ, Javis gọi tool lấy số thật
    "summarize my orders" -> LỌT qua đường tắt tiết kiệm token. Đường tắt cố ý KHÔNG phát
                             tool nào, nên model không có cách nào biết số đơn hàng, và nó
                             làm cái tệ nhất: bịa ra một con số nghe hợp lý.

Cùng một câu hỏi, hai ngôn ngữ, hai kết cục. Nguyên nhân: mẫu DENY của cổng có `don hang`
nhưng không có `orders`. Tiếng Anh được phục vụ một nửa, và **nửa bộ từ vựng nguy hiểm hơn
không có bộ từ vựng nào** - tiếng Thái không khớp gì cả nên rơi về đường đầy đủ, an toàn;
tiếng Anh khớp ALLOW rồi lọt.

File này khoá lại cả hai hướng: tiếng Việt phải giữ NGUYÊN hành vi cũ từng bit, và tiếng Anh
phải được chặn ngang bằng.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import sys

import lang as lang_mod
import lang_registry
import lexicon
from fast_path_runtime import FastIntentClassifier
import readonly_path_runtime
import readonly_orchestrator
import chatbot_runtime
import chatbot_store

_loi = []


def check(ten, dieu_kien):
    print(f"       {'ok  ' if dieu_kien else 'FAIL'} {ten}")
    if not dieu_kien:
        _loi.append(ten)


# ============================================================
# 1. Dò ngôn ngữ
# ============================================================
check("dấu tiếng Việt là tín hiệu chắc chắn",
      lang_mod.detect("tóm tắt đơn hàng hôm nay giúp anh")[0] == "vi")
check("tiếng Việt KHÔNG DẤU vẫn dò ra (người Việt gõ kiểu này rất nhiều)",
      lang_mod.detect("toi muon xem doanh thu thang nay the nao")[0] == "vi")
check("tiếng Anh dò ra qua hư từ",
      lang_mod.detect("summarize my orders for this quarter please")[0] == "en")

# Bẫy đã cắn một lần: câu tiếng Nhật mở đầu bằng KANJI, mà kanji nằm trong khoảng Hán. Duyệt
# từng ký tự rồi trả về ngay khi khớp thì câu đó ra "zh".
check("tiếng Nhật mở đầu bằng kanji vẫn ra ja, không ra zh",
      lang_mod.detect("今日の売上をまとめてください")[0] == "ja")
check("tiếng Thái ra th", lang_mod.detect("สรุปยอดขายวันนี้ให้หน่อยครับ")[0] == "th")
check("câu quá ngắn thì KHÔNG đoán bừa", lang_mod.detect("ok")[0] == "")


# ============================================================
# 2. Built-in responses remain English; input detection remains available to safety gates.
# ============================================================
# Đổi ở 0.35.0: `resolve` KHÔNG còn tự chốt ngôn ngữ trả lời khi không có ai ghim. Nó trả
# `theo_nguoi_dung=True` và prompt bảo model bám theo thứ tiếng người dùng vừa viết.
#
# Vì sao bỏ: bản trước tự dò tự chốt, và đo được nó làm tệ hơn model - dò tiếng Anh 16/18,
# còn người viết tiếng Thái/Nhật/Pháp/Tây Ban Nha thì LUÔN bị trả lời tiếng Việt vì mấy thứ
# tiếng đó không có trong sổ đăng ký. Model bám đúng cho mọi thứ tiếng, miễn phí.
for _c in ("trả lời bằng tiếng Việt", "Please answer in French", "こんにちは"):
    _d = lang_mod.resolve(turn_text=_c, reply_pref="vi", chatbot_pin="fr", brain_pin="ja")
    check(f"assistant output is English regardless of legacy pins or input: {_c}",
          _d.lang == "en" and not _d.theo_nguoi_dung)
    check("input detection remains available", _d.lang_cau_hoi == lang_mod.detect(_c)[0])

_khoi = lang_mod.khoi_ngon_ngu(lang_mod.resolve(turn_text="trả lời bằng tiếng Việt"))
check("system language contract requires English and preserves quotations",
      "clear, natural English" in _khoi and "verbatim" in _khoi)
check("English fallback prompt does not mirror user language",
      "Answer in English." == lang_mod.nudge_dau_luot("vi"))


# ============================================================
# 3. Cổng đường tắt: tiếng Việt giữ nguyên, tiếng Anh phải ngang bằng
# ============================================================
_gate = FastIntentClassifier()

# Hành vi tiếng Việt phải giống hệt trước khi rút regex ra lexicon.
for cau in ("Đính kèm file này giúp anh", "Doanh thu hôm nay bao nhiêu",
            "Gửi email cho khách giúp anh", "Đặt lịch họp ngày mai"):
    check(f"VI vẫn bị chặn: {cau[:34]}", not _gate.classify(cau).eligible)
check("VI tự chứa vẫn đi tắt được", _gate.classify("Giải thích entropy là gì").eligible)
check("VI viết lách vẫn đi tắt được",
      _gate.classify("Viết cho anh 5 tiêu đề về học tập").eligible)

# Đây là bệnh chính file này sinh ra để chặn.
_cap = [
    ("tóm tắt đơn hàng", "summarize my orders"),
    ("doanh thu tháng này bao nhiêu", "how much did we make this month"),
    ("nhắc tôi 7h sáng mai", "remind me tomorrow at 7am"),
    ("sửa file ghi chú giúp anh", "edit my notes file"),
    ("kiểm tra hộp thư giúp anh", "check my inbox"),
]
for vi_cau, en_cau in _cap:
    v = _gate.classify(vi_cau).eligible
    e = _gate.classify(en_cau).eligible
    check(f"VI và EN cùng kết cục: {en_cau[:30]}", v == e is False)

check("EN tự chứa vẫn đi tắt được", _gate.classify("explain what entropy is").eligible)
check("EN tính toán vẫn đi tắt được khi biết ngôn ngữ",
      _gate.classify("calculate 15 percent of 2400", lang="en").eligible)
# Chưa dò ra ngôn ngữ thì cổng TỪ CHỐI, KỂ CẢ khi câu có một chữ trông rất "tự chứa". Cho đi
# tắt là tự nhận mình hiểu một câu mình chưa đọc được ngôn ngữ; cái giá của việc từ chối chỉ
# là token, và đó là cái giá phải trả.
check("chưa rõ ngôn ngữ thì không đi tắt, dù câu có chữ hợp lệ của ALLOW",
      not _gate.classify("translate zbcd qwerty mnop vlkx").eligible)

# Tiếng Việt CÓ DẤU và tiếng Âu có dấu phải tách được nhau ra: một chữ "de" trong câu tiếng
# Pháp từng đủ để cả câu bị chấm thành tiếng Việt, rồi Javis trả lời người Pháp bằng tiếng Việt.
check("tiếng Pháp KHÔNG bị nhận thành tiếng Việt",
      lang_mod.detect("Peux-tu me résumer les ventes du mois de juin ?")[0] != "vi")
check("tiếng Tây Ban Nha cũng vậy",
      lang_mod.detect("¿Cuánto vendimos este mes en la tienda?")[0] != "vi")
check("nhưng tiếng Việt KHÔNG DẤU viết ngắn vẫn phải dò ra",
      lang_mod.detect("entropy la gi")[0] == "vi")

# `lang_cau_hoi` chỉ nhận thứ dò được từ CHÍNH lượt này. Bản trước còn mượn ngôn ngữ của
# phiên khi câu quá ngắn; bỏ luôn cùng với tầng phiên, và bỏ là ĐÚNG hướng: mượn tức là đoán,
# mà cổng chặn đoán sai thì đem nhầm bộ từ vựng ra chấm.
_dq = lang_mod.resolve(turn_text="calculate 15 percent of 2400")
check("dò được từ chính lượt thì cổng dùng luôn",
      _dq.lang_cau_hoi == "en" and _gate.classify("calculate 15 percent of 2400",
                                                  lang=_dq.lang_cau_hoi).eligible)
check("câu quá ngắn thì cổng KHÔNG có ngôn ngữ, và phải suy biến an toàn",
      lang_mod.resolve(turn_text="cho anh xem").lang_cau_hoi == "")
# Ngôn ngữ GHIM tuyệt đối không rò xuống cổng: nó nói Javis trả lời tiếng gì, không nói người
# dùng đang viết tiếng gì.
check("ngôn ngữ ghim KHÔNG rò xuống cổng",
      lang_mod.resolve(turn_text="cho anh xem", reply_pref="en").lang_cau_hoi == "")
check("và ghim cũng không che mất ngôn ngữ THẬT của câu hỏi",
      lang_mod.resolve(turn_text="anh muốn xem doanh thu tháng này",
                       reply_pref="en").lang_cau_hoi == "vi")


# ============================================================
# 4. Luật suy biến: thiếu bộ từ vựng làm Javis TỐN HƠN, không làm Javis LỎNG HƠN
# ============================================================
_th = _gate.classify("สรุปยอดขายวันนี้ให้หน่อยครับ")
check("ngôn ngữ chưa có lexicon thì KHÔNG được đi tắt", not _th.eligible)
check("và lý do phải nói rõ là vì thiếu lexicon, không phải 'uncertain' do may",
      "no_lexicon" in _th.reason)

_ja = _gate.classify("今日の売上をまとめてください")
check("tiếng Nhật cũng vậy", not _ja.eligible and "no_lexicon" in _ja.reason)

check("lexicon chưa có thì get() trả None chứ không im lặng dùng tạm tiếng Việt",
      lexicon.get("th") is None)
check("mọi lexicon phải khai ĐỦ các tập bắt buộc",
      all(all(hasattr(lexicon.get(m), t) for t in lexicon.BAT_BUOC)
          for m in lexicon.ma_list()))


# ============================================================
# 5. Hai cổng chỉ đọc
# ============================================================
for mod, ten in ((readonly_path_runtime, "readonly_path"), (readonly_orchestrator, "orchestrator")):
    for cau in ("Đặt lịch họp ngày mai", "Đăng bài lên trang"):
        check(f"{ten} chặn ý định ghi tiếng Việt: {cau[:26]}",
              mod._cong_chi_doc(mod._norm(cau), cau) == "write_intent")
    for cau in ("Schedule a meeting for tomorrow", "Post this to the page"):
        check(f"{ten} chặn ý định ghi tiếng Anh: {cau[:26]}",
              mod._cong_chi_doc(mod._norm(cau), cau) == "write_intent")


# ============================================================
# 6. Chatbot chuyên trách: ngôn ngữ của bot ĐỘC LẬP với ngôn ngữ của chủ
# ============================================================
check("new chatbots default to English", chatbot_store._clean_ngon_ngu(None) == "en")
check("legacy auto and Vietnamese chatbot settings migrate to English",
      chatbot_store._clean_ngon_ngu("auto") == "en" and chatbot_store._clean_ngon_ngu("vi") == "en")
check("unknown chatbot language falls back to English", chatbot_store._clean_ngon_ngu("xx") == "en")

_p_auto = chatbot_runtime.build_bot_prompt({"name": "Assistant", "ngon_ngu": "auto"})
_p_en = chatbot_runtime.build_bot_prompt({"name": "Trợ lý", "ngon_ngu": "en"})
check("legacy auto bot prompt is English-only", "clear, natural English" in _p_auto)
check("English bot prompt keeps the same policy", "clear, natural English" in _p_en)
check("prompt bot ALWAYS carries English policy",
      "English-only product policy" in chatbot_runtime.build_bot_prompt({"name": "Assistant"}))


# ============================================================
# 7. Sổ đăng ký
# ============================================================
check("chuẩn hoá được mã dạng đầy đủ", lang_registry.chuan_hoa("vi-VN") == "vi")
check("mã lạ trả rỗng chứ không tự rơi về mặc định", lang_registry.chuan_hoa("xx") == "")
check("get() falls back to English", lang_registry.get("xx").code == "en")
check("ElevenLabs cố ý để rỗng (giọng của nó vốn đa ngôn ngữ)",
      lang_registry.giong_tts("en", "elevenlabs") == "")
check("Edge có giọng riêng cho từng ngôn ngữ",
      lang_registry.giong_tts("vi", "edge") != lang_registry.giong_tts("en", "edge"))

print()
if _loi:
    print(f"ĐỎ {len(_loi)} mục: " + "; ".join(_loi[:5]))
    sys.exit(1)
print("Tất cả xanh.")
