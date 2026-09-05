# -*- coding: utf-8 -*-
"""生成模拟教材 PDF（仅用于本地冒烟测试，非交付物）
用法: python make_test_pdf.py out.pdf
生成 6 页带中文内容的"教材"，每页页脚带印刷页码（从 10 开始，模拟 offset=9）
"""
import sys
from pathlib import Path

from fpdf import FPDF

CONTENT = [
    # (印刷页码, 标题, 段落列表)
    (10, "第一章 电路模型和电路定律",
     ["电路理论研究的对象是实际电路。为了便于分析，常把实际器件抽象为理想元件模型，如电阻、电感、电容和电源。",
      "基尔霍夫电流定律（KCL）指出：对于任一集总电路中的任一节点，在任一时刻，流入该节点的电流之和等于流出该节点的电流之和。",
      "基尔霍夫电压定律（KVL）指出：对于任一集总电路中的任一回路，在任一时刻，沿该回路所有支路电压的代数和恒等于零。"]),
    (11, "1-2 电阻元件与欧姆定律",
     ["线性电阻元件满足欧姆定律：u = Ri，其中 R 为电阻，单位为欧姆。",
      "当电流与电压取关联参考方向时，电阻消耗的功率为 p = ui = Ri^2 = u^2 / R。",
      "注意：电阻元件是耗能元件，其功率恒为正值，不可能向外电路释放能量。"]),
    (12, "1-3 电压源与电流源",
     ["理想电压源的端电压恒定，与流过它的电流无关；理想电流源的输出电流恒定，与其端电压无关。",
      "实际电源可以用理想电压源串联内阻或理想电流源并联内导来等效。",
      "受控源是四端元件，常见类型有电压控制电压源（VCVS）、电流控制电压源（CCVS）、电压控制电流源（VCCS）和电流控制电流源（CCCS）。"]),
    (13, "第二章 电阻电路的等效变换",
     ["电阻串联时等效电阻等于各电阻之和：R = R1 + R2 + ... + Rn。",
      "电阻并联时等效电导等于各电导之和，两电阻并联的等效电阻为 R = R1*R2/(R1+R2)。",
      "分压公式：串联电阻上电压按电阻大小分配；分流公式：并联电阻上电流按电导大小分配。"]),
    (14, "2-3 戴维南定理与诺顿定理",
     ["戴维南定理：任一线性含源二端网络，对外电路而言，可用一个电压源与电阻串联的支路等效，电压源等于该网络的开路电压 uoc，电阻等于该网络中所有独立源置零后的等效电阻 Req。",
      "诺顿定理：任一线性含源二端网络，可用一个电流源与电阻并联的支路等效，电流源等于该网络的短路电流 isc，电阻仍为 Req。",
      "开路电压与短路电流之间满足 uoc = Req * isc，两者可以互相换算。"]),
    (15, "2-4 最大功率传输定理",
     ["当负载电阻等于含源二端网络的等效电阻（RL = Req）时，负载获得最大功率，此即为最大功率传输条件，也称阻抗匹配。",
      "最大功率为 Pmax = uoc^2 / (4 * Req)。",
      "注意：在最大功率传输条件下，电源效率只有 50%，传输效率与功率最大不能同时兼顾。"]),
]


class TextBookPDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("song", size=9)
        self.cell(0, 10, f"第 {self.cur_page_no} 页", align="C")

    @property
    def cur_page_no(self):
        # 通过对象级状态记录当前印刷页码
        return getattr(self, "_printed_no", 0)

    def set_printed_no(self, n):
        self._printed_no = n


def main(out_path: str = "test_textbook.pdf"):
    pdf = TextBookPDF()
    pdf.add_font("song", "", r"C:\Windows\Fonts\simsun.ttc", uni=True)
    pdf.set_auto_page_break(auto=True, margin=20)

    for printed_no, title, paras in CONTENT:
        pdf.add_page()
        pdf.set_printed_no(printed_no)
        pdf.set_font("song", size=16)
        pdf.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_font("song", size=12)
        for p in paras:
            pdf.multi_cell(0, 8, p)
            pdf.ln(3)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    pdf.output(out_path)
    print(f"OK: {out_path} ({pdf.pages_count} pages, printed 10..15)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "test_textbook.pdf")
