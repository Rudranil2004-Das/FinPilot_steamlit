import io, sqlite3
from datetime import date, timedelta
import pandas as pd
import streamlit as st
from finance_service import analyze_transaction, analyze_bill, categorize_transaction

st.set_page_config(page_title="FinPilot | Personal Finance", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
DB = "finpilot.db"
CATEGORIES = ["Groceries", "Utilities", "Transport", "Shopping", "Healthcare", "Subscriptions", "Rent & Housing", "Education", "Income", "Transfer", "Other"]

def connect():
    con = sqlite3.connect(DB, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, tx_date TEXT NOT NULL, description TEXT NOT NULL, amount REAL NOT NULL, category TEXT NOT NULL, tx_type TEXT NOT NULL DEFAULT 'Expense', budget REAL NOT NULL DEFAULT 0, review_probability REAL NOT NULL DEFAULT 0, source TEXT NOT NULL DEFAULT 'Manual')''')
    con.execute('''CREATE TABLE IF NOT EXISTS bills (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, amount REAL NOT NULL, due_date TEXT NOT NULL, available REAL NOT NULL, consequence TEXT, priority TEXT, shortfall REAL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    con.commit()
    if con.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 0:
        rows = [
            ((date.today()-timedelta(days=1)).isoformat(),'Weekly groceries',1850,'Groceries','Expense',3000,.08,'Demo'),
            ((date.today()-timedelta(days=3)).isoformat(),'Monthly electricity bill',1450,'Utilities','Expense',2000,.08,'Demo'),
            ((date.today()-timedelta(days=5)).isoformat(),'Wireless headphones',7999,'Shopping','Expense',2500,.72,'Demo'),
            ((date.today()-timedelta(days=7)).isoformat(),'Metro card recharge',600,'Transport','Expense',1200,.08,'Demo'),
            ((date.today()-timedelta(days=10)).isoformat(),'Monthly salary',28000,'Income','Income',0,.02,'Demo'),
        ]
        con.executemany('INSERT INTO transactions(tx_date,description,amount,category,tx_type,budget,review_probability,source) VALUES(?,?,?,?,?,?,?,?)', rows); con.commit()
    return con

def money(x): return f"₹{float(x):,.0f}"
def load_transactions(con): return pd.read_sql_query('SELECT * FROM transactions ORDER BY tx_date DESC, id DESC', con)
def add_transaction(con, tx_date, description, amount, category, tx_type, budget, risk, source='Manual'):
    con.execute('INSERT INTO transactions(tx_date,description,amount,category,tx_type,budget,review_probability,source) VALUES(?,?,?,?,?,?,?,?)', (str(tx_date),description,float(amount),category,tx_type,float(budget),float(risk),source)); con.commit()

with st.sidebar:
    st.markdown("<div style='font-size:13px;letter-spacing:3px;color:#8da6c7;font-weight:700'>FINPILOT / PERSONAL</div><h1 style='padding-top:4px'>Finance, in focus.</h1>", unsafe_allow_html=True)
    page = st.radio("WORKSPACE", ["Dashboard", "Transactions", "Smart review", "Bill planner", "Insights & export"], label_visibility="visible")
    st.divider()
    st.caption("LOCAL-FIRST • DEMO DATA")
    st.caption("Your entries are stored in a local SQLite database on this computer.")
con = connect()
df = load_transactions(con)
expenses = df[df.tx_type == 'Expense'] if not df.empty else df
income = float(df.loc[df.tx_type=='Income','amount'].sum()) if not df.empty else 0
spend = float(expenses.amount.sum()) if not expenses.empty else 0

st.markdown("<style>.block-container{padding-top:2rem;padding-bottom:3rem}.stMetric{background:#101d2b;padding:16px 18px;border:1px solid #24364a;border-radius:14px}.stButton>button{border-radius:9px;font-weight:600}.small-muted{color:#93a4b8}</style>", unsafe_allow_html=True)
if page == "Dashboard":
    st.markdown("## Good evening. <span style='color:#80aaff'>Here's your money snapshot.</span>", unsafe_allow_html=True)
    st.caption(f"A clear view of recorded activity · {date.today().strftime('%d %b %Y')} · INR")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Total recorded income", money(income)); c2.metric("Recorded expenses", money(spend)); c3.metric("Net recorded flow", money(income-spend)); c4.metric("Needs review", int((expenses.review_probability>=.5).sum()) if not expenses.empty else 0)
    left,right=st.columns([1.45,1])
    with left:
        st.markdown("### Spending by category")
        if expenses.empty: st.info("Add a transaction to start your dashboard.")
        else:
            chart=expenses.groupby('category',as_index=False).amount.sum().sort_values('amount',ascending=False)
            st.bar_chart(chart.set_index('category')['amount'], height=280)
    with right:
        st.markdown("### Review queue")
        flagged=expenses[expenses.review_probability>=.5] if not expenses.empty else expenses
        if flagged.empty: st.success("Nothing currently meets the review threshold.")
        else:
            for _,r in flagged.head(4).iterrows():
                st.warning(f"**{r['description']}** · {money(r['amount'])}\n\nReview score: {r['review_probability']:.0%}")
    st.markdown("### Latest activity")
    if df.empty: st.info("No activity recorded yet.")
    else:
        view=df[['tx_date','description','category','tx_type','amount','source']].head(8).copy(); view['amount']=view.amount.map(money)
        st.dataframe(view, hide_index=True, use_container_width=True)
    st.caption("Demo records are fictional. Review scores are transparent rule-based signals, not fraud determinations or financial advice.")

elif page == "Transactions":
    st.markdown("## Transactions")
    st.caption("Add everyday activity and keep a searchable, persistent ledger.")
    tab1,tab2=st.tabs(["＋ Add transaction", "Ledger & filters"])
    with tab1:
        with st.form('add_tx', clear_on_submit=True):
            a,b=st.columns(2); tx_date=a.date_input('Date', value=date.today()); tx_type=b.selectbox('Type',['Expense','Income'])
            description=st.text_input('Description', placeholder='e.g. Groceries from local market')
            c,d,e=st.columns(3); amount=c.number_input('Amount (₹)', min_value=1.0, value=500.0, step=100.0); category=d.selectbox('Category',CATEGORIES); budget=e.number_input('Usual budget (₹)',min_value=0.0,value=1500.0,step=100.0)
            submitted=st.form_submit_button('Save transaction', type='primary', use_container_width=True)
        if submitted:
            if not description.strip(): st.error('Enter a description before saving.')
            else:
                if category=='Other': category=categorize_transaction(description)[0]
                risk=analyze_transaction(description,amount,max(budget,1))['review_probability'] if tx_type=='Expense' else .02
                add_transaction(con,tx_date,description.strip(),amount,category,tx_type,budget,risk)
                st.success('Transaction saved to your local ledger.'); st.rerun()
    with tab2:
        all_df=load_transactions(con)
        q=st.text_input('Search description or category')
        cats=st.multiselect('Category',sorted(all_df.category.unique()) if not all_df.empty else CATEGORIES, default=sorted(all_df.category.unique()) if not all_df.empty else CATEGORIES)
        filtered=all_df[all_df.category.isin(cats)] if not all_df.empty else all_df
        if q and not filtered.empty: filtered=filtered[filtered.apply(lambda r:q.lower() in str(r.description).lower() or q.lower() in str(r.category).lower(),axis=1)]
        st.dataframe(filtered[['id','tx_date','description','category','tx_type','amount','budget','review_probability','source']] if not filtered.empty else filtered, hide_index=True,use_container_width=True)
        with st.expander('Delete a transaction'):
            if not all_df.empty:
                selected=st.selectbox('Choose transaction',all_df.id.tolist(),format_func=lambda i:f"#{i} · {all_df.loc[all_df.id==i,'description'].iloc[0]}")
                if st.button('Delete selected transaction'):
                    con.execute('DELETE FROM transactions WHERE id=?',(int(selected),)); con.commit(); st.success('Transaction deleted.'); st.rerun()

elif page == "Smart review":
    st.markdown("## Smart transaction review")
    st.caption("Categorization + budget-aware risk signals, calculated locally. No API key required.")
    with st.form('review_form'):
        desc=st.text_input('What was the transaction?',placeholder='e.g. Unknown online electronics payment')
        a,b=st.columns(2); amount=a.number_input('Amount (₹)',min_value=1.0,value=5000.0,step=250.0); budget=b.number_input('Usual budget (₹)',min_value=1.0,value=2000.0,step=250.0)
        save=st.checkbox('Save result to transaction ledger',value=True)
        go=st.form_submit_button('Analyze transaction',type='primary')
    if go:
        try:
            st.session_state['review_result'] = analyze_transaction(desc,amount,budget)
            st.session_state['review_save'] = save
        except ValueError as e: st.error(str(e))
    result=st.session_state.get('review_result')
    if result:
        x,y,z=st.columns(3); x.metric('Suggested category',result['category']); y.metric('Review signal',f"{result['review_probability']:.0%}"); z.metric('Amount vs budget',f"{result['budget_ratio']:.1f}×")
        st.progress(result['review_probability'],text='Rule-based review signal')
        if result['review_probability']>=.5 or result['budget_exceeded']: st.warning('Consider checking the merchant, receipt, and account activity. This is not proof of fraud.')
        else: st.success('No strong review signal from the configured rules.')
        st.markdown('### Why this result?')
        reasons=[]
        if result['budget_exceeded']: reasons.append(f"Amount is {result['budget_ratio']:.1f}× the usual budget.")
        if result['amount']>=25000: reasons.append('The amount crosses the high-value review threshold (₹25,000).')
        if any(w in result['description'].lower() for w in ['unknown','unrecognized','not mine','unauthorised','unauthorized']): reasons.append('Description contains an unfamiliar-transaction keyword.')
        if not reasons: reasons.append('Amount and description do not trigger the stronger configured rules.')
        for reason in reasons: st.write('• '+reason)
        st.caption(f"Category match confidence: {result['category_confidence']:.0%}. This is a heuristic estimate, not a trained ML confidence score.")
        if st.session_state.get('review_save',False):
            if st.button('Confirm and save this analysis',type='primary'):
                add_transaction(con,date.today(),result['description'],result['amount'],result['category'],'Expense',result['usual_budget'],result['review_probability'],'Smart review')
                st.session_state.pop('review_result',None); st.session_state.pop('review_save',None)
                st.success('Saved. Open Transactions to see it.')

elif page == "Bill planner":
    st.markdown("## Bill planner")
    st.caption("Prioritize bills by due date, funding gap, and late-payment consequences.")
    with st.form('bill_form'):
        name=st.text_input('Bill name',placeholder='Electricity bill')
        a,b=st.columns(2); amount=a.number_input('Bill amount (₹)',min_value=1.0,value=2400.0,step=100.0); due=b.date_input('Due date',value=date.today()+timedelta(days=3))
        funds=st.number_input('Money available for this bill (₹)',min_value=0.0,value=1800.0,step=100.0)
        consequence=st.text_area('Late-payment consequence',placeholder='Late fee, service interruption, etc.')
        submit=st.form_submit_button('Assess and save bill',type='primary')
    if submit:
        try:
            result=analyze_bill(name,amount,due.isoformat(),funds,consequence)
            con.execute('INSERT INTO bills(name,amount,due_date,available,consequence,priority,shortfall) VALUES(?,?,?,?,?,?,?)',(name,amount,due.isoformat(),funds,consequence,result['priority'],result['shortfall'])); con.commit()
            a,b,c=st.columns(3); a.metric('Priority',result['priority']); b.metric('Days until due',result['days_remaining']); c.metric('Funding gap',money(result['shortfall']))
            if result['shortfall']>0: st.warning(f"You are short by {money(result['shortfall'])}. Review essential expenses and contact the bill provider if needed.")
            elif result['days_remaining']<=1: st.warning('This bill is due very soon or overdue.')
            else: st.success('The available funds cover this bill on their own.')
        except ValueError as e: st.error(str(e))
    st.markdown('### Saved bills')
    bills=pd.read_sql_query('SELECT id,name,amount,due_date,available,priority,shortfall FROM bills ORDER BY due_date ASC',con)
    if bills.empty: st.info('Bills you assess will appear here.')
    else: st.dataframe(bills,use_container_width=True,hide_index=True)

else:
    st.markdown("## Insights & export")
    st.caption("Review the patterns in your recorded data or export it for Excel / Power BI.")
    if not expenses.empty:
        monthly=expenses.copy(); monthly['month']=pd.to_datetime(monthly.tx_date).dt.to_period('M').astype(str)
        st.markdown('### Monthly expense trend'); st.line_chart(monthly.groupby('month').amount.sum())
        st.markdown('### Category breakdown'); st.dataframe(expenses.groupby('category').amount.agg(['sum','count','mean']).sort_values('sum',ascending=False).rename(columns={'sum':'Total ₹','count':'Transactions','mean':'Average ₹'}),use_container_width=True)
    else: st.info('Record expenses to unlock insights.')
    export=load_transactions(con)
    st.download_button('Download transactions as CSV',export.to_csv(index=False).encode('utf-8-sig'),'finpilot_transactions.csv','text/csv',type='primary')
    bill_export=pd.read_sql_query('SELECT * FROM bills ORDER BY due_date',con)
    st.download_button('Download bills as CSV',bill_export.to_csv(index=False).encode('utf-8-sig'),'finpilot_bills.csv','text/csv')
    st.divider()
    st.markdown('### Import transactions from CSV')
    st.write('Required columns: `description`, `amount`. Optional: `tx_date`, `category`, `tx_type`, `budget`.')
    upload=st.file_uploader('Choose CSV file',type=['csv'])
    if upload:
        try:
            incoming=pd.read_csv(upload); incoming.columns=[c.strip().lower() for c in incoming.columns]
            if not {'description','amount'}.issubset(incoming.columns): st.error('CSV needs description and amount columns.')
            else:
                st.dataframe(incoming.head(10),use_container_width=True)
                if st.button('Import these rows',type='primary'):
                    imported=0
                    for _,r in incoming.iterrows():
                        desc=str(r['description']).strip()
                        try: amt=float(r['amount'])
                        except: continue
                        if not desc or amt<=0: continue
                        cat=str(r.get('category') or categorize_transaction(desc)[0]); typ=str(r.get('tx_type') or 'Expense').title(); typ=typ if typ in ['Income','Expense'] else 'Expense'
                        dt=str(r.get('tx_date') or date.today().isoformat())[:10]; budget=float(r.get('budget') or max(amt,1))
                        risk=analyze_transaction(desc,amt,max(budget,1))['review_probability'] if typ=='Expense' else .02
                        add_transaction(con,dt,desc,amt,cat,typ,budget,risk,'CSV import'); imported+=1
                    st.success(f'Imported {imported} valid rows.'); st.rerun()
        except Exception as e: st.error(f'Could not read this CSV: {e}')
    with st.expander('Reset demo data'):
        st.warning('This deletes all transactions and bills in the local FinPilot database and restores sample transactions.')
        if st.button('Reset all local data'):
            con.execute('DELETE FROM transactions'); con.execute('DELETE FROM bills'); con.commit(); con.close(); import os; os.remove(DB) if __import__('os').path.exists(DB) else None; st.success('Local demo data reset.'); st.rerun()
con.close()
