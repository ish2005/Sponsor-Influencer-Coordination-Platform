from flask import app, Flask,render_template,request,redirect, url_for
import sqlite3
import  matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
app=Flask(__name__)
def stats(role,username):
    with sqlite3.connect('database.db') as conn:
        cursor=conn.cursor()
        if role=='admin':
            earnings_per_sponsor=cursor.execute('''
            SELECT s_name, SUM(payment_amount) as total_earnings
            FROM ad_request
            WHERE  status = "accept"
            GROUP BY s_name
        ''').fetchall()
            earnings_per_influencer=cursor.execute('''SELECT username, SUM(payment_amount) as total_earnings
            FROM ad_request
            WHERE status = "accept"
            GROUP BY username
        ''').fetchall()
            earnings_per_campaign=cursor.execute('select description,sum(payment_amount) from ad_request group by description having status="accept"').fetchall()         
            platform_influencer=cursor.execute('select platform,count(platform) from influencer group by platform').fetchall()
            industry_sponsor=cursor.execute('select industry,count(industry) from sponsor group by industry').fetchall() 
            return earnings_per_sponsor,earnings_per_influencer,earnings_per_campaign,platform_influencer,industry_sponsor      
        elif role=='influencer':
            name=cursor.execute('select username from influencer where i_name= ?',(username,)).fetchone()
            name=name[0]
            campaigns1=cursor.execute('select description from ad_request where username = ? and status="accept"',(name,)).fetchall()
            campaigns=[campaign[0] for campaign in campaigns1]
            ids1=cursor.execute('select id from ad_request where username = ? and status="accept"',(name,)).fetchall()
            ids=[id[0] for id in ids1]
            earnings=cursor.execute('select sum(earnings) from influencer where username = ?',(name,)).fetchall()[0][0]
            earning_ineach_campaign=cursor.execute('select description,payment_amount from ad_request where username = ? and status="accept"',(name,)).fetchall()
            earning_percompany=cursor.execute('select s_name,payment_amount from ad_request where username = ? and status="accept" group by s_name',(name,)).fetchall()
            duration_time=[]
            if  ids:
                for id in ids:
                    start_date,end_date=cursor.execute('''select c.start_date,c.end_date from campaign c where id = ?'''
                                                    ,(id,)).fetchall()[0]
                    duration_time.append(duration(start_date,end_date))
            return campaigns,ids,earnings,earning_ineach_campaign,earning_percompany,duration_time
        elif role=='sponsor':
            earnings_per_campaign=cursor.execute('select description,sum(payment_amount) from ad_request group by description having s_name = ? and status="accept"',(username,)).fetchall()         
            earnings_per_influencer=cursor.execute('''
            SELECT username, SUM(payment_amount) as total_earnings
            FROM ad_request
            WHERE s_name = ? AND status = "accept"
            GROUP BY username
        ''',(username,)).fetchall()
            status_campaigns=cursor.execute('select status,count(status) from ad_request where s_name=? group by status ',(username,))
            return earnings_per_campaign,earnings_per_influencer,status_campaigns                       
def duration(start_date_str, end_date_str, date_format="%Y-%m-%d"):
    from datetime import datetime
    start_date = datetime.strptime(start_date_str, date_format)
    end_date = datetime.strptime(end_date_str, date_format)
    duration = end_date - start_date
    return duration.days
def calculate_progress(start_date, end_date):
    from datetime import datetime
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    today = datetime.today()
    total_duration = (end_date - start_date).days
    elapsed_duration = (today - start_date).days
    if elapsed_duration < 0:
        return 0
    elif elapsed_duration > total_duration:
        return 100
    return (elapsed_duration / total_duration) * 100
def update_query(role,id,username,action,budget):
    if role=="Sponsor":
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('update ad_request set status= ? where id = ?',(action,id))
            cursor.execute('update campaign set spent= spent + ? where id = ? ',(budget,id))
            if action=='accept':
                cursor.execute('update influencer set earnings= earnings + ? where username = ? ',(budget,username))
            conn.commit()
    elif role=="Influencer":
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('update ad_request set status= ? where id = ?',(action,id))
            cursor.execute('update campaign set spent= spent + ? where id = ? ',(budget,id))
            if action=='accept':
                cursor.execute('update influencer set earnings= earnings + ? where username = ? ',(budget,username))
            conn.commit()
@app.route("/")
def home():
    return render_template("home.html")
@app.route('/sponsor_dashboard/<sponsor_name>/stats',methods=['GET','POST'])
def sponsor_stats(sponsor_name):
    earnings_per_campaign,earnings_per_influencer,status_campaigns=stats(role='sponsor',username=sponsor_name)
    categories, values = zip(*earnings_per_campaign)
    bar_width = 0.4
    plt.bar(categories, values,width=bar_width, color='skyblue')
    plt.xlabel('Campaign Names')
    plt.ylabel('Spent')
    plt.title('Bar Chart of Money Spent on Campaigns (in millions)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    save_path_1 = rf'C:\Users\Admin\Desktop\MAD-1 PROJECT\Brand Dealzz\static\sponsor_bar_chart_1_{sponsor_name}.png'
    plt.savefig(save_path_1)
    plt.close()
    categories, values = zip(*earnings_per_influencer)
    bar_width = 0.4
    plt.bar(categories, values,width=bar_width, color='skyblue',align='center')
    plt.xlabel('Influencers')
    plt.ylabel('Earnings')
    plt.title('Bar Chart of Money Spent on Influencers (in Ten  millions)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    save_path_2 = rf'C:\Users\Admin\Desktop\MAD-1 PROJECT\Brand Dealzz\static\sponsor_bar_chart_2_{sponsor_name}.png'
    plt.savefig(save_path_2)
    plt.close()
    labels, values = zip(*status_campaigns)
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.title("Pie Chart of Request Status")
    save_path_3 = rf'C:\Users\Admin\Desktop\MAD-1 PROJECT\Brand Dealzz\static\sponsor_pie_chart_{sponsor_name}.png'
    plt.savefig(save_path_3)
    plt.close()
    return render_template('sponsor stats.html',sponsor_name=sponsor_name)

@app.route('/influencer_dashboard/<influencer_name>/stats',methods=['GET','POST'])
def influencer_stats(influencer_name):
    campaigns,ids,earnings,earning_ineach_campaign,earning_percompany,duration_time=stats('influencer',influencer_name)
    if campaigns and duration_time:
        plt.bar( campaigns,duration_time, color='skyblue')
        plt.title('Bar Chart for Duration of Campaigns (in days)')
        plt.xlabel('Campaigns')
        plt.ylabel('Duration')
        save_path_1 = rf'C:\Users\Admin\Desktop\MAD-1 PROJECT\Brand Dealzz\static\influencer_bar_chart_1_{influencer_name}.png'
        plt.savefig(save_path_1)
        plt.close()
        labels,values=zip(*earning_ineach_campaign)
        plt.bar( labels,values, color='skyblue')
        plt.title('Bar Chart for Earnings in Campaigns ')
        plt.xlabel('Campaigns')
        plt.ylabel('Earnings')
        save_path_2 = rf'C:\Users\Admin\Desktop\MAD-1 PROJECT\Brand Dealzz\static\influencer_bar_chart_2_{influencer_name}.png'
        plt.savefig(save_path_2)
        plt.close()
        labels, values = zip(*earning_percompany)
        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')
        plt.title("Pie Chart of Earnings from Each Company")
        save_path_3 = rf'C:\Users\Admin\Desktop\MAD-1 PROJECT\Brand Dealzz\static\influencer_pie_chart_{influencer_name}.png'
        plt.savefig(save_path_3)
        plt.close()
    return render_template('influencer stats.html',earnings=earnings,influencer_name=influencer_name)
@app.route('/admin/stats', methods=['GET', 'POST'])
def admin_stats():
    earnings_per_sponsor,earnings_per_influencer,earnings_per_campaign,platform_influencer,industry_sponsor=stats('admin',None)   
    labels,values=zip(*earnings_per_sponsor)
    plt.ylim(0, 60000)
    plt.bar( labels,values, color='skyblue',width=0.2)
    plt.title('Bar Chart for Sponsors Spent on Campaigns ')
    plt.xlabel('Sponsor')
    plt.ylabel('Spent on Campaigns')
    save_path_1 = r'C:\Users\Admin\Desktop\MAD-1 PROJECT\Brand Dealzz\static\admin_bar_chart_1.png'
    plt.savefig(save_path_1)
    plt.close()
    labels1,values1=zip(*earnings_per_influencer)
    plt.ylim(0, 10000000)
    plt.bar( labels1,values1, color='skyblue',width=0.2)
    plt.title('Bar Chart for Earnings by Influencer ')
    plt.xlabel('Influencer')
    plt.ylabel('Earnings')
    save_path_2 = r'C:\Users\Admin\Desktop\MAD-1 PROJECT\Brand Dealzz\static\admin_bar_chart_2.png'
    plt.savefig(save_path_2)
    plt.close()
    labels3,values3=zip(*earnings_per_campaign)
    plt.ylim(0, 10000000)
    plt.bar( labels3,values3, color='skyblue',width=0.2)
    plt.title('Bar Chart for Budget Spent on each Campaign ')
    plt.xlabel('Campaigns')
    plt.ylabel('Budget Spent')
    save_path_3 = r'C:\Users\Admin\Desktop\MAD-1 PROJECT\Brand Dealzz\static\admin_bar_chart_3.png'
    plt.savefig(save_path_3)
    plt.close()
    labels4, values4 = zip(*platform_influencer)
    plt.pie(values4, labels=labels4, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.title("Pie Chart of Platforms of Influencers")
    save_path_4 = r'C:\Users\Admin\Desktop\MAD-1 PROJECT\Brand Dealzz\static\admin_pie_chart_1.png'
    plt.savefig(save_path_4)
    plt.close()
    labels5, values5 = zip(*industry_sponsor)
    plt.pie(values5, labels=labels5, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.title("Pie Chart of Industry of Sponsors")
    save_path_5 = r'C:\Users\Admin\Desktop\MAD-1 PROJECT\Brand Dealzz\static\admin_pie_chart_2.png'
    plt.savefig(save_path_5)
    plt.close()
    return render_template('admin stats.html')
@app.route('/Influencer_Register', methods=['GET','POST'])
def influencer_register():
    if request.method=='POST':
        try:
            i_name = request.form['name']
            platform = request.form['platform']
            typ_of_content = request.form['type_of_content']
            followers = int(request.form['followers'])
            userid = request.form['userid']
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            with sqlite3.connect('database.db') as con:
                cursor = con.cursor()
                cursor.execute('''
                    INSERT INTO influencer (
                        i_name, platform, typ_of_content, followers, userid,
                         email,username,earnings
                    ) VALUES (?, ?, ?, ?, ?, ?, ?,0)
                ''', (i_name, platform, typ_of_content, followers, userid, email,username))
                
                con.commit()
                cursor.execute('''
                    INSERT INTO user (
                        username,password,role
                    ) VALUES (?,?,'influencer')
                ''', (username,password))
                con.commit()
                return render_template('Influencer Register.html')
        except Exception as e:
        # Handle any exceptions that occur during registration
            return f"An error occurred: {str(e)}"
    return render_template('Influencer Register.html')  # Assuming this is your success page
@app.route('/Sponser_Register', methods=['GET','POST'])
def sponsor_register():
    if request.method=='POST':
            try:
                s_name = request.form['name']
                industry = request.form['industry']
                most_selling = request.form['most_selling']
                years = int(request.form['years'])
                username = request.form['username']
                password = request.form['password']
                email = request.form['email']
                with sqlite3.connect('database.db') as con:
                    cursor = con.cursor()
                    cursor.execute('''
                        INSERT INTO  sponsor (
                            s_name, industry, most_selling, years,
                            email,username
                        ) VALUES (?, ?, ?, ?, ?,?)
                    ''',(s_name,industry,most_selling,years, email,username))
                    con.commit()
                    cursor.execute('''
                    INSERT INTO user (
                        username, password,role
                    ) VALUES (?, ?,'sponsor')
                ''', (username,password))
                    con.commit()
                    return render_template('Sponser Register.html')
            except Exception as e:
                return f"An error occurred: {str(e)}"
    return render_template('Sponser Register.html')
@app.route('/userlogin',methods=['GET','POST'])
def User_login():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        with sqlite3.connect('database.db') as con:
            cursor = con.cursor()
            role=cursor.execute('SELECT role FROM user WHERE username = ? AND password = ?', (name, password)).fetchall()
            print(role)
            if role:
                if role[0][0]=='influencer':
                    i_name=cursor.execute('SELECT i_name FROM influencer WHERE username = ?', (name,)).fetchone()
                    return redirect(url_for('influencer_dashboard', influencer_name=i_name[0]))
                elif role[0][0]=='sponsor':
                    cursor.execute('SELECT s_name FROM sponsor WHERE username = ?', (name,))
                    s_name=cursor.fetchone()
                    return redirect(url_for('sponsor_dashboard', sponsor_name=s_name[0]))
                elif role[0][0]=='admin':
                    return redirect(url_for('admin'))
            else:
                return 'Incorrect username or password'
    
    return render_template('User login.html')
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        cursor.execute('''
       SELECT 
    c.start_date,
    c.end_date,
    c.budget,
    ar.description,
    c.niche,
    ar.status,
    c.s_name,
    ar.username,c.flag
FROM 
    campaign c
JOIN 
    ad_request ar 
ON 
    c.description = ar.description
WHERE 
    ar.description IN (SELECT description FROM ad_request) 
    AND ar.status = "accept" and c.flag=0
''')
        campaigns = cursor.fetchall()
        campaign_data = [
                        {
                            'name': campaign[6],
                            'description': campaign[3],
                            'niche': campaign[4],
                            'start_date': campaign[0],
                            'end_date': campaign[1],
                            'budget': campaign[2],
                            'username':campaign[7],
                            'progress': calculate_progress( campaign[0],campaign[1])
                        }
                        for campaign in campaigns
                    ]
        
    return render_template('admin.html',campaigns=campaign_data)
@app.route('/admin/flaggedcampaigns', methods=['GET', 'POST'])
def admin_f_camp():
    with sqlite3.connect('database.db') as conn:
        campaigns = conn.execute('SELECT * FROM campaign where flag = 1').fetchall()
        influencers = conn.execute('SELECT * FROM influencer where flag = 1').fetchall()
        campaign_data = [
                            {
                                'id': campaign[0],
                                'createdby':campaign[1],
                                'name': campaign[7],
                                'description': campaign[2],
                                'niche': campaign[3],
                                'start_date': campaign[4],
                                'end_date': campaign[5],
                                'budget': campaign[6],
                                'progress':calculate_progress( campaign[4],campaign[5])
                                
                            }
                            for campaign in campaigns
                        ]
        influencer_data=[
            {
                'name':influencer[1],
                'niche': influencer[2],
                'followers':influencer[3],
                'Platform':influencer[6],
                'Platform_username':influencer[4],
                'email':influencer[5],
                'earnings':influencer[8],
                'username':influencer[7]
            }
            for influencer in influencers
        ]
        if request.method == 'POST':
            request_id = request.form.get('request')
            action = request.form.get('action')
            if request_id.isnumeric():
                with sqlite3.connect('database.db') as con:
                    cursor=con.cursor()
                    cursor.execute('Delete from campaign  where id = ?',(request_id,))
                    try:
                        cursor.execute('Delete from ad_request  where id = ?',(request_id,))
                        con.commit()
                    except:
                        pass
                    con.commit()
            else:
                with sqlite3.connect('database.db') as con:
                    cursor=con.cursor()
                    cursor.execute('Delete from influencer where username = ?',(request_id,))
                    con.commit() 
                    try:
                        cursor.execute('Delete from ad_request where username = ?',(request_id,))
                        cursor.execute('Delete from user where username = ?',(request_id,))
                    except:
                        pass                    
                    con.commit()         
    return render_template('admin flagged campaigns.html',sponsors=campaign_data,influencers=influencer_data)

@app.route('/admin/find', methods=['GET', 'POST'])
def admin_find():
    with sqlite3.connect('database.db') as conn:
        campaigns = conn.execute('SELECT * FROM campaign').fetchall()
        influencers = conn.execute('SELECT * FROM influencer').fetchall()
        campaign_data = [
                            {
                                'id': campaign[0],
                                'createdby':campaign[1],
                                'name': campaign[7],
                                'description': campaign[2],
                                'niche': campaign[3],
                                'start_date': campaign[4],
                                'end_date': campaign[5],
                                'budget': campaign[6],
                                'progress':calculate_progress( campaign[4],campaign[5])
                                
                            }
                            for campaign in campaigns
                        ]
        influencer_data=[
            {
                'name':influencer[1],
                'niche': influencer[2],
                'followers':influencer[3],
                'Platform':influencer[6],
                'Platform_username':influencer[4],
                'email':influencer[5],
                'earnings':influencer[8],
                'username':influencer[7]
            }
            for influencer in influencers
        ]
        if request.method == 'POST':
            request_id = request.form.get('request')
            action = request.form.get('action')
            if request_id.isnumeric():
                with sqlite3.connect('database.db') as con:
                    cursor=con.cursor()
                    cursor.execute('update campaign set flag = ? where id = ?',(action,request_id,))
                    con.commit()
            else:
                with sqlite3.connect('database.db') as con:
                    cursor=con.cursor()
                    cursor.execute('update influencer set flag = ? where username = ?',(action,request_id,))
                    con.commit()         
    return render_template('admin find.html',sponsors=campaign_data,influencers=influencer_data)
@app.route('/sponsor_dashboard/<sponsor_name>', methods=['GET', 'POST'])
def sponsor_dashboard(sponsor_name):
    if request.method == 'POST':
        c_name = request.form.get('name')
        description = request.form.get('description')
        niche = request.form.get('niche')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        budget = request.form.get('budget')
        
        if c_name and description and niche and start_date and end_date and budget:
            with sqlite3.connect('database.db') as con:
                cursor = con.cursor()
                cursor.execute('''
                    INSERT INTO campaign (name, description, niche, start_date, end_date, budget, s_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (c_name, description, niche, start_date, end_date, int(budget), sponsor_name))
                con.commit()
    
    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        try:
            cursor.execute('SELECT * FROM campaign WHERE s_name = ?', (sponsor_name,))
            campaigns = cursor.fetchall()
        except Exception as e:
            return f'{e}'
        
        if campaigns:
            campaign_data = [
                {
                    'id': campaign[0],
                    'name': campaign[1],
                    'description': campaign[2],
                    'niche': campaign[3],
                    'start_date': campaign[4],
                    'end_date': campaign[5],
                    'budget': campaign[6],
                    'progress': calculate_progress(campaign[4], campaign[5])
                }
                for campaign in campaigns
            ]
        else:
            campaign_data = []

    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        try:
            cursor.execute('SELECT * FROM ad_request WHERE s_name = ? and request_by != ?' , (sponsor_name,sponsor_name))
            ad_requests = cursor.fetchall()
        except Exception as e:
            return f'{e}'
        
        ad_requests = [
            {
                'id': request[1],
                'username': request[2],
                'payment_amount': request[4],
                'status': request[5],
                'description': request[6]
            }
            for request in ad_requests
            if request[5]=='Pending'
        ]

    if request.method == 'POST':
        request_id = request.form.get('request_id')
        action = request.form.get('action')
        amount= request.form.get('budget')
        username= request.form.get('username')

        if request_id and action:
            update_query('Sponsor', request_id,username, action,amount)

    return render_template('s_dashboard.html', sponsor_name=sponsor_name, campaigns=campaign_data, ad_requests=ad_requests)
@app.route('/influencer_dashboard/<influencer_name>/status',methods=['GET','POST'])
def extract_ad_requests(influencer_name):
    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        cursor.execute("SELECT s_name, payment_amount, status FROM ad_request where i_name = ?",(influencer_name,))
        rows = cursor.fetchall()

    return render_template('i_status.html',ad_requests=rows,influencer_name=influencer_name)
@app.route('/influencer_dashboard/<influencer_name>/campaigns',methods=['GET','POST'])
def get_ad_requests(influencer_name):
    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        cursor.execute('''
                SELECT c.s_name, ar.description, c.niche, c.start_date, c.end_date
        FROM campaign c, ad_request ar 
        where ar.description=c.description and i_name = ? AND status = "accept"''',(influencer_name,))
        rows = cursor.fetchall()
        campaigns=[ {
            'name':c[0],
            'description':c[1],
            'niche':c[2],
            'start_date':c[3],
            'end_date':c[4],
            'progress':calculate_progress(c[3],c[4])
        }
        for c in rows 
        
        ]



    return render_template('i_campaigns.html',campaigns=campaigns,influencer_name=influencer_name)
           

@app.route('/sponsor_dashboard/<sponsor_name>/find',methods=['GET','POST'])
def find(sponsor_name):
    with sqlite3.connect('database.db') as conn:
        campaigns = conn.execute('SELECT * FROM campaign where s_name = ?',(sponsor_name,)).fetchall()
        influencers = conn.execute('SELECT * FROM influencer').fetchall()
        campaign_data = [
                            {
                                'id': campaign[0],
                                'name': campaign[1],
                                'description': campaign[2],
                                'niche': campaign[3],
                                'start_date': campaign[4],
                                'end_date': campaign[5],
                                'budget': campaign[6],
                                'progress':calculate_progress( campaign[4],campaign[5])
                                
                            }
                            for campaign in campaigns
                        ]
        influencer_data=[
            {
                'name':influencer[1],
                'niche': influencer[2],
                'followers':influencer[3],
                'Platform':influencer[6]

            }
            for influencer in influencers
        ]
        if request.method == 'POST':
            data = request.form
            campaign_name = data['campaign_name']
            campaign_description = data['campaign_description']
            campaign_budget = data['campaign_budget']
            username = data['username']
            with sqlite3.connect('database.db') as conn:
                cursor = conn.cursor()
                cursor.execute('select username from influencer where i_name =?',(username,))
                i_name=cursor.fetchone()
                cursor.execute('select id from campaign where description =?',(campaign_description,))
                id=cursor.fetchone()
                cursor.execute('''insert into ad_request (id,username,s_name,payment_amount,status,description,i_name
                               ,request_by) values(?,?,?,?,?) ''',(id[0],i_name[0],sponsor_name,campaign_budget,"Pending",campaign_description,sponsor_name,username))
                conn.commit()
    return render_template('s_find.html',role='Sponsor', campaigns=campaign_data, influencers=influencer_data,sponsor_name=sponsor_name)
@app.route('/sponsor_dashboard/<sponsor_name1>/<sponsor_name>/request_influencer', methods=['POST'])
def request_influencer(sponsor_name1,sponsor_name):
     data = request.form
     try:
        if data:
            campaign_name = data['campaign_name']
            campaign_description = data['campaign_description']
            campaign_budget = data['campaign_budget']
            username = data['username']
            with sqlite3.connect('database.db') as conn:
                        cursor = conn.cursor()
                        row=cursor.execute('select s_name from campaign where description = ?',(campaign_description,)).fetchone()
                        cursor = conn.cursor()
                        cursor.execute('select username from influencer where i_name =?',(username,))
                        i_name=cursor.fetchone()
                        cursor.execute('select id from campaign where description =?',(campaign_description,))
                        id=cursor.fetchone()
            with sqlite3.connect('database.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute('''INSERT INTO ad_request (id,i_name,username, s_name, payment_amount, status, description, request_by) 
                  VALUES (?,?,?, ?, ?, ?, ?, ?)''',(id[0],username,i_name[0],row[0],campaign_budget,"Pending",campaign_description,row[0]))
                        conn.commit()
            return redirect(url_for('sponsor_dashboard', sponsor_name=row[0]))

     except Exception as e:
         return f'{e}'
@app.route('/logout')
def logout():
    return render_template('home.html')
@app.route('/sponsor_dashboard/<sponsor_name>/on_going_campaigns', methods=['GET','POST'])
def campaigns(sponsor_name):
    with sqlite3.connect('database.db') as con:
            cursor = con.cursor()
            cursor.execute('''
       SELECT 
    c.start_date,
    c.end_date,
    c.budget,
    ar.description,
    c.niche,
    i.i_name,
    ar.status
FROM 
    campaign c
JOIN 
    ad_request ar ON ar.description = c.description
JOIN 
    influencer i ON ar.username = i.username
WHERE 
    c.s_name = ? AND ar.s_name = ? and ar.status="accept"
''',(sponsor_name,sponsor_name,))
            campaigns = cursor.fetchall()
            campaign_data = [
                        {
                            'name': campaign[5],
                            'description': campaign[3],
                            'niche': campaign[4],
                            'start_date': campaign[0],
                            'end_date': campaign[1],
                            'budget': campaign[2],
                            'progress': calculate_progress( campaign[0],campaign[1])
                        }
                        for campaign in campaigns
                    ]

    return render_template('s_campaigns.html', campaigns=campaign_data,sponsor_name=sponsor_name)
@app.route('/influencer_dashboard/<influencer_name>',methods=['GET','POST'])
def influencer_dashboard(influencer_name):
    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        username=cursor.execute('select username from influencer where i_name=?',(influencer_name,)).fetchone()
        earnings=cursor.execute('select earnings from  influencer where i_name=?',(influencer_name,)).fetchone()
        try:
            cursor.execute('SELECT * FROM ad_request WHERE i_name = ? and request_by != ?' , (influencer_name,username[0]))
            requests = cursor.fetchall()
        except Exception as e:
            return f'{e}'
        
        ad_requests = [
            {
                'id':request[1],
                'name': request[2],
                'username': request[3],
                'payment_amount': request[4],
                'status': request[5],
                'description': request[6]
            }
            for request in requests
            if request[5]=='Pending'
        ]

    if request.method == 'POST':
        request_id = request.form.get('request_id')
        action = request.form.get('action')
        username= request.form.get('username')
        budget=request.form.get('budget')
        if request_id and action:
            update_query('Influencer', request_id,username, action,budget)
    return render_template('i_dashboard.html',influencer_name=influencer_name,ad_requests=ad_requests,earnings=earnings[0]
                           ) 
@app.route('/influencer_dashboard/<influencer_name>/find',methods=['GET','POST'])
def i_find(influencer_name):
    with sqlite3.connect('database.db') as conn:
        cursor=conn.cursor()
        campaigns = conn.execute('SELECT * FROM campaign').fetchall()
        userid1=cursor.execute('select username from influencer where i_name = ?',(influencer_name,)).fetchall()
        userid=userid1[0][0]
        campaign_data = [
            {
                'id': campaign[0],
                'name': campaign[1],
                'description': campaign[2],
                'niche': campaign[3],
                'start_date': campaign[4],
                'end_date': campaign[5],
                'budget': campaign[6],
                'progress': calculate_progress(campaign[4], campaign[5])
            }
            for campaign in campaigns
            
        ]
        

    if request.method == 'POST' and 'id' in request.form:
        campaign_id = request.form.get('id')
        with sqlite3.connect('database.db') as con:
            cursor = con.cursor()
            try:
                cursor.execute('SELECT * FROM campaign WHERE id = ?', (campaign_id,))
                s_campaign = cursor.fetchone()
                if s_campaign:
                    c_id = s_campaign[0]
                    payment_amount = s_campaign[6]
                    s_name = s_campaign[7] 
                    request_by=influencer_name
                    description=s_campaign[2]
                    cursor.execute('''
                        INSERT INTO ad_request (id, username,i_name, s_name, payment_amount, status,request_by,description)
                        VALUES (?, ?, ?, ?, ?, ?,?,?)
                    ''', (c_id, userid,influencer_name, s_name,  payment_amount , 'Pending',request_by,description))
                    con.commit()
            except Exception as e:
                return f'Error fetching campaign details: {e}'

    return render_template('i_find.html', influencer_name=influencer_name, campaign_data=campaign_data)
app.run(debug=True)