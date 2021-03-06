'''
This script creates a python interface to a database of fundamental X-ray
fluorescence parameters compiled by W.T. Elam, B.D. Ravel and J.R. Sieber,
published in Radiation Physics and Chemistry, 63 (2), 121 (2002). The
database is published by NIST at
http://www.cstl.nist.gov/acd/839.01/xrfdownload.html

'''
import io
import json
import os
import sqlite3
import sys


def create_database(source, dest, overwrite=False):
    source_file_name = source
    dest_file_name = dest

    if os.path.isfile(dest_file_name):
        if overwrite:
            os.remove(dest_file_name)
        else:
            return

    with io.open(source_file_name, encoding='ascii') as f:
        lines = f.readlines()
        while lines[0].startswith('/'):
            lines.pop(0)

    conn = sqlite3.connect(dest_file_name)
    c = conn.cursor()

    c.execute(
        '''create table elements (atomic_number integer, element text,
        atomic_mass real, density real)
        '''
        )
    current_edge_id = 0
    c.execute(
        '''create table absorption_edges (id integer, element text, label text,
        energy real, fluorescence_yield real, jump_ratio real)
        '''
        )
    current_line_id = 0
    c.execute(
        '''create table emission_lines (id integer, element text,
        iupac_symbol text, siegbahn_symbol text, start_level text,
        end_level text, energy real, intensity real)
        '''
        )
    current_ck_id = 0
    c.execute(
        '''create table Coster_Kronig
        (id integer, element text, start_level text, end_level text,
        transition_probability real, total_transition_probability real)
        '''
        )
    current_photo_id = 0
    c.execute(
        '''create table photoabsorption (id integer, element text,
        log_energy text, log_photoabsorption text,
        log_photoabsorption_spline text)
        '''
        )
    current_scatter_id = 0
    c.execute(
        '''create table scattering (id integer, element text, log_energy text,
        log_coherent_scatter text, log_coherent_scatter_spline text,
        log_incoherent_scatter text, log_incoherent_scatter_spline text)
        '''
        )

    while lines:
        line = lines.pop(0)
        if line.startswith('Element'):
            sym, num, mw, rho = line.split()[1:]
            c.execute(
                'insert into elements values (?,?,?,?)', (num, sym, mw, rho)
                )
            current_element = sym
        elif line.startswith('Edge'):
            current_edge_id += 1
            label, energy, yield_, jump = line.split()[1:]
            el = current_element
            c.execute(
                'insert into absorption_edges values (?,?,?,?,?,?)',
                (current_edge_id, el, label, energy, yield_, jump)
                )
            current_edge = label
        elif line.startswith('  Lines'):
            while True:
                if lines[0].startswith('    '):
                    current_line_id += 1
                    line = lines.pop(0)
                    iupac, siegbahn, energy, intensity = line.split()
                    end, start = iupac.split('-')
                    el = current_element
                    c.execute(
                        'insert into emission_lines values (?,?,?,?,?,?,?,?)',
                        (current_line_id, el, iupac, siegbahn, start, end,
                        energy, intensity)
                        )
                else:
                    break
        elif line.startswith('  CK '):
            temp = line.split()[1:]
            ck = []
            while temp:
                (i,j), temp = temp[:2], temp[2:]
                ck.append((i,j))
            if lines[0].startswith('  CKtotal'):
                temp = lines.pop(0).split()[1:]
                ck_total = []
                while temp:
                    (i,j), temp = temp[:2], temp[2:]
                    ck_total.append((i,j))
            else:
                ck_total = ck
            for i, j in zip(ck, ck_total):
                current_ck_id += 1
                (so, p), tp = i[:], j[1]
                c.execute(
                    '''insert into Coster_Kronig
                    values (?,?,?,?,?,?)''',
                    (current_ck_id, current_element, so, current_edge,
                    p, tp)
                    )
        elif line.startswith('Photo'):
            current_photo_id += 1
            energy = []
            photo = []
            spline = []
            while lines[0].startswith('    '):
                temp = [float(i) for i in lines.pop(0).split()]
                energy.append(temp[0])
                photo.append(temp[1])
                spline.append(temp[2])
            c.execute(
                'insert into photoabsorption values (?,?,?,?,?)',
                (current_photo_id, current_element, json.dumps(energy),
                json.dumps(photo), json.dumps(spline))
                )
        elif line.startswith('Scatter'):
            current_scatter_id += 1
            energy = []
            cs = []
            css = []
            ics = []
            icss = []
            while lines[0].startswith('    '):
                temp = [float(i) for i in lines.pop(0).split()]
                energy.append(temp[0])
                cs.append(temp[1])
                css.append(temp[2])
                ics.append(temp[3])
                icss.append(temp[4])
            c.execute(
                'insert into scattering values (?,?,?,?,?,?,?)',
                (current_scatter_id, current_element, json.dumps(energy),
                json.dumps(cs), json.dumps(css), json.dumps(ics),
                json.dumps(icss))
                )

    conn.commit()

    c.close()


if __name__ == '__main__':
    create_database('elam_physical_reference/elam.dat', 'elam.db', True)
