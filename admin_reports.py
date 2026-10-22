"""Módulo separado de reportes y exportación, solo para administradores."""
from flask import render_template, request, Response
from datetime import date
import csv, io

def init_report_routes(app, db_factory, admin_required):
    @app.route('/admin/reportes')
    @admin_required
    def admin_reports():
        start=request.args.get('desde',date.today().replace(day=1).isoformat()); end=request.args.get('hasta',date.today().isoformat())
        sql='SELECT a.id,u.name,u.email,a.movement,a.timestamp,a.note FROM attendance a JOIN users u ON u.id=a.user_id WHERE substr(a.timestamp,1,10) BETWEEN ? AND ? ORDER BY a.timestamp DESC'
        with db_factory() as c:
            rows=c.execute(sql,(start,end)).fetchall()
            totals=c.execute('SELECT movement,COUNT(*) total FROM attendance WHERE substr(timestamp,1,10) BETWEEN ? AND ? GROUP BY movement',(start,end)).fetchall()
        return render_template('reports.html',rows=rows,desde=start,hasta=end,totals=totals)

    @app.route('/admin/reportes/exportar')
    @admin_required
    def admin_export_csv():
        start=request.args.get('desde',date.today().replace(day=1).isoformat()); end=request.args.get('hasta',date.today().isoformat())
        with db_factory() as c:
            rows=c.execute('SELECT a.id,u.name,u.email,a.movement,a.timestamp,a.note FROM attendance a JOIN users u ON u.id=a.user_id WHERE substr(a.timestamp,1,10) BETWEEN ? AND ? ORDER BY a.timestamp DESC',(start,end)).fetchall()
        out=io.StringIO(newline=''); w=csv.writer(out); w.writerow(['ID','Colaborador','Correo','Movimiento','Fecha y hora','Nota'])
        for r in rows: w.writerow([r['id'],r['name'],r['email'],r['movement'],r['timestamp'],r['note']])
        return Response('\ufeff'+out.getvalue(),mimetype='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="asistencia_{start}_{end}.csv"'})
