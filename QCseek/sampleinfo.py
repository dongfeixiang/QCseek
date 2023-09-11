
# conn = pymysql.connect(
#     host='139.224.83.66',
#     user='erp_readonly',
#     password='aLfQH4getbyht2br7CLX',
#     database='sanyou_erp',
#     port=5367,
#     charset='utf8'
# )
# pn = "P55604"
# with conn.cursor() as cursor:
#     sql = f"SELECT * FROM stock_sample WHERE merge_no='{pn}'"
#     cursor.execute(sql)
#     res = cursor.fetchone()
#     if res is not None:
#         # 蛋白编号
#         no = res[5]
#         # 名称
#         name = res[6]
#         # 属性
#         prop = json.loads(res[11])
#         # 批号
#         batch = prop["58"]
#         # buffer
#         buffer = prop["67"]
#         # 分子量
#         mw = prop["64"]
#         # 等电点
#         pi = prop["65"]
#         # 消光系数
#         exco = prop["66"]
#         # 浓度
#         conc = prop["150"]
#         print(no, name, batch, buffer, mw, pi, exco, conc)

# ('stock_sample',)

# 0 (('id', 'bigint', 'NO', 'PRI', None, 'auto_increment'),
# 1 ('company_id', 'bigint', 'YES', 'MUL', None, ''),
# 2 ('prefix', 'varchar(255)', 'YES', '', None, ''),
# 3 ('no', 'varchar(50)', 'YES', '', None, ''),
# 4 ('batch', 'int', 'YES', '', None, ''),
# 5 ('merge_no', 'varchar(255)', 'YE 'YES', '', None, ''),
# 6 ('privacy_id', 'int', 'YES', '', None, ''),
# 7 ('temperature_id', 'bigint', 'YES', '', None, ''),
# 8 ('property', 'varchar(2000)', 'YES', '', None, ''),
# ('warning_num', 'decimal(20,3)', 'YES', '', None, ''),
# ('remark', 'varchar(255)', 'YES', '', None, ''),
# ('state', 'bigint', 'YES', '', None, ''),
# ('days', 'int', 'YES', '', None, ''),
# ('total_num', 'decimal(20,8)', 'YES', '', None, ''),
# ('need_show', 'tinyint(1)', 'YES', '', None, ''),
# ('from_type', 'int', 'YES', '', None, ''),
# ('create_time', 'datetime', 'YES', '', None, ''),
# ('del', 'tinyint(1)', 'YES', '', None, ''),
# ('update_time', 'datetime', 'NO', '', 'CURRENT_TIMESTAMP', 'DEFAULT_GENERATED on
# update CURRENT_TIMESTAMP'))

# temp = cv2.imread("temp.png")
# img = cv2.imread("sds.png")
# temp[40:, 60:] = cv2.resize(img, (200, 720))
# cv2.imshow("", temp)
# cv2.waitKey()
# # sds = SDS.get(SDS.id==40002)
# # sec = SEC.get(SEC.id==13002)
# # row = QCRow(sds.pid, sds, sec, None)
# # generate_coa(row)
