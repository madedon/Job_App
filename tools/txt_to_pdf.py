"""Convert CV and cover letter .txt files to professional PDF format.

Usage: python tools/txt_to_pdf.py <application_folder>
Example: python tools/txt_to_pdf.py applications/2026-03-05_Okta_Director_Strategic_Initiatives
"""
import sys, io, os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

from fpdf import FPDF


class CVtoPDF(FPDF):
    def header(self): pass
    def footer(self): pass


def is_role_title(line, months):
    has_date = any(m in line for m in months)
    return has_date and (' to ' in line) and (',' in line)


def create_cv_pdf(input_path, output_path):
    pdf = CVtoPDF(orientation='P', unit='mm', format='Letter')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=15, top=15, right=15)
    pdf.add_page()

    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    lines = text.split('\n')
    w = pdf.w - pdf.l_margin - pdf.r_margin
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    current_section = None
    bullet_indent = 4
    bullet_char = '-'

    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(2)
            continue
        if line == 'DIMITRIOS TSELIOS':
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_x(pdf.l_margin)
            pdf.cell(w=w, h=7, text=line, align='C', new_x='LMARGIN', new_y='NEXT')
            continue
        if line.startswith('Frisco, TX'):
            pdf.set_font('Helvetica', '', 8)
            pdf.set_x(pdf.l_margin)
            pdf.cell(w=w, h=5, text=line, align='C', new_x='LMARGIN', new_y='NEXT')
            pdf.ln(2)
            continue
        if line.isupper() and len(line) > 3 and 'DIMITRIOS' not in line:
            current_section = line
            pdf.ln(2)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_x(pdf.l_margin)
            pdf.cell(w=w, h=6, text=line, new_x='LMARGIN', new_y='NEXT')
            y = pdf.get_y()
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.ln(2)
            continue
        if is_role_title(line, months):
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(w=w, h=5, text=line, new_x='LMARGIN', new_y='NEXT')
            continue
        if line.startswith('Recognized'):
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(w=w, h=5, text=line, new_x='LMARGIN', new_y='NEXT')
            continue
        if current_section == 'PROFESSIONAL EXPERIENCE':
            pdf.set_font('Helvetica', '', 9)
            pdf.set_x(pdf.l_margin)
            pdf.cell(w=bullet_indent, h=4.5, text=bullet_char)
            bullet_w = w - bullet_indent
            pdf.multi_cell(w=bullet_w, h=4.5, text=line, new_x='LMARGIN', new_y='NEXT')
        else:
            pdf.set_font('Helvetica', '', 9)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(w=w, h=4.5, text=line, new_x='LMARGIN', new_y='NEXT')

    pdf.output(output_path)
    print(f'CV PDF created: {output_path}')


def create_cl_pdf(input_path, output_path):
    pdf = CVtoPDF(orientation='P', unit='mm', format='Letter')
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(left=25, top=25, right=25)
    pdf.add_page()

    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    lines = text.split('\n')
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_font('Helvetica', '', 10.5)

    sig_items = ['Dimitrios Tselios', 'dimitrios.tselios@gmail.com',
                 '+1 469 562 3045',
                 'https://www.linkedin.com/in/dimitriostselios076/']

    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(4)
            continue
        if line in sig_items:
            pdf.set_font('Helvetica', '', 10)
            pdf.set_x(pdf.l_margin)
            pdf.cell(w=w, h=5, text=line, new_x='LMARGIN', new_y='NEXT')
            pdf.set_font('Helvetica', '', 10.5)
            continue
        if line == 'Sincerely,':
            pdf.ln(2)
            pdf.set_x(pdf.l_margin)
            pdf.cell(w=w, h=5.5, text=line, new_x='LMARGIN', new_y='NEXT')
            pdf.ln(6)
            continue
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(w=w, h=5.5, text=line, new_x='LMARGIN', new_y='NEXT')

    pdf.output(output_path)
    print(f'Cover letter PDF created: {output_path}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python tools/txt_to_pdf.py <application_folder>')
        sys.exit(1)

    folder = sys.argv[1]
    cv_file = None
    for f in os.listdir(folder):
        if f.startswith('Dimitrios_Tselios_') and f.endswith('.txt'):
            cv_file = f
            break
    if not cv_file:
        cv_file = 'optimized_cv.txt'

    cv_txt = os.path.join(folder, cv_file)
    cv_pdf = os.path.join(folder, cv_file.replace('.txt', '.pdf'))
    cl_txt = os.path.join(folder, 'cover_letter.txt')
    role_part = cv_file.replace('Dimitrios_Tselios_', '').replace('.txt', '')
    cl_pdf = os.path.join(folder, f'Dimitrios_Tselios_Cover_Letter_{role_part}.pdf')

    if os.path.exists(cv_txt):
        create_cv_pdf(cv_txt, cv_pdf)
    else:
        print(f'CV not found: {cv_txt}')

    if os.path.exists(cl_txt):
        create_cl_pdf(cl_txt, cl_pdf)
    else:
        print(f'Cover letter not found: {cl_txt}')
