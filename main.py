from App import *

@login_manager.user_loader #для доступа нужно авторизоваться
@app.route('/busket') #корзина
def busket():
    items=db.session.query(
        Item,ItemInBusket).filter(Item.id==ItemInBusket.item_id,ItemInBusket.user_id==current_user.id).all()
    return render_template('Busket.html',items=items,collections=Collection.query.all(),user_=current_user,col=None)

@app.route('/') #главная страница
def main():
    return render_template(
        'ShopMain.html',collections=Collection.query.all(),title='Главная страница',col=None,user_=current_user)

@app.route('/tovary/<int:id_>/busket',methods=['post']) #добавление товара в корзину
def add_to_busket(id_):
    im=Item.query.filter_by(id=id_).first().image
    data=ItemInBusket(user_id=current_user.id,item_id=id_)
    db.session.add(data)
    db.session.commit()
    return redirect(url_for('busket'))

@app.route('/tovary/<int:id_>/') #страница товара
def item_page(id_):
    data=Item.query.filter_by(id=id_).first()
    c=Collection.query.filter_by(id=data.collect).first()
    return render_template('product.html',item=data,collections=Collection.query.all(),
                           title=data.title,user_=current_user,
                           comments=Comment.query.filter_by(item_id=data.id).all(),col=c)

@app.route('/tovary/<int:id_>/comment',methods=['post']) #сохранение отзыва
def comment(id_):
    user=User.query.filter_by(id=current_user.id).first()
    text=request.form['comment']
    #form = AddCommentForm()
    if text!='':
        data=Comment(body=text,username=user.name,item_id=id_)
        db.session.add(data)
        db.session.commit()
    return redirect(url_for('item_page',id_=id_))

@login_manager.user_loader #загрузка пользователя
def load_user(user_id):
    return db.session.query(User).get(user_id)

@app.route('/add_collect') #страница добавления раздела
def add_collect():
    if current_user.id!=1: #доступно только админу
        return redirect(url_for('main'))
    return render_template('AddingCollect.html',col=None,collections=Collection.query.all(),
                           user_=current_user)

@app.route('/add_coll',methods=['post']) #добавление раздела
def add_coll():
    data=Collection(title=request.form['link'],trans=request.form['title'])
    db.session.add(data)
    db.session.commit()
    return redirect(url_for('add_collect'))

@app.route('/add_item') #страница добавления товара
def add_item():
    if current_user.id!=1: #доступно только админу
        return redirect(url_for('main'))
    return render_template('Adding.html',col=None,collections=Collection.query.all(),
                           user_=current_user)

@app.route('/add_file',methods=['post']) #добавление товаров из файла xlsx
def add_file():
    file=request.files['excel']
    data=pd.DataFrame(file.filename)
    for i in data.index:
        one=data.iloc[0]
        name=one['name']
        price=one['price']
        image=one['image']
        descript=one['descr']
        coll=one['collection']
        db.session.add(Item(title=name,descr=descript,price=price,image=image,
              collect=coll))
    db.session.commit()
    return redirect('/add_item')

@app.route('/add',methods=['post']) #добавление товара
def add():
    colls=[c.trans for c in Collection.query.all()]
    name=request.form['name']
    price=request.form['price']
    image=request.form['image']
    descript=request.form['descr']
    coll=request.form['collection']
    if coll in colls:
        data=Item(title=name,descr=descript,price=price,image=image,
              collect=coll)
        #else:
        #new=Collection()
        db.session.add(data)
        db.session.commit()
    return render_template('Adding.html',col=None,collections=Collection.query.all(),
                           user_=current_user)

@app.route('/delete/<int:item>',methods=['POST']) #удаление из корзины
def delete_busket(item):
    item = ItemInBusket.get(id=item)
    db.session.delete(item)
    db.session.commit()
    return redirect('busket')

@app.route('/login',methods=['GET', 'POST']) #авторизация
def login():
    login_=request.form.get('login')
    password=request.form.get('password')
    if login_ and password:
        user=User.query.filter_by(name=login_).first()
        try:
            user.password
        except:
            return flash('Error')
        else:
            if check_password_hash(user.password,password):
                login_user(user,remember=True)
                return redirect(url_for('main'))
            else:
                return flash('Error')
    flash('Fill both fields')
    return render_template('ShopLogin.html',title='Вход',user_=current_user)

@app.route('/<string:collect>/') #страницы отдельных разделов
@app.route('/<string:collect>/<int:page>')
def page(collect,page=None):
    try:
        bus=[g.item_id for g in ItemInBusket.query.filter_by(user_id=current_user.id).all()] #товары в корзине
    except:
        bus=[]
    if collect in [col.title for col in Collection.query.all()]:
        col=Collection.query.filter_by(title=collect).first().id
        goods=db.session.query(Item,Collection).filter(Item.collect==Collection.id).filter_by(collect=col)
        if page in (None,1):
            return render_template('ShopGoods.html',goods=goods.paginate(1,number,False),collections=Collection.query.all()
                                   ,col=Collection.query.filter_by(title=collect).first(),user_=current_user,bus=bus)
            #return redirect(url_for('first_page',collect=collect))
        return render_template('ShopGoods.html',goods=goods.paginate(page,number,False),collections=Collection.query.all(),
                               col=Collection.query.filter_by(title=collect).first().title,user_=current_user,bus=bus)

@app.route('/tovary/') #все товары
@app.route('/tovary/page=<int:page>')
def all_(page=None):
    try:
        bus=[g.item_id for g in ItemInBusket.query.filter_by(user_id=current_user.id).all()] #товары в корзине
    except:
        bus=[]
    goods=db.session.query(Item,Collection).filter(Item.collect==Collection.id)
    if page in (None,1):
        return render_template('ShopGoods.html',goods=goods.paginate(1,number,False),user_=current_user,bus=bus,
                                   collections=Collection.query.all(),col=Collection(title='tovary',trans='Все товары'))
    return render_template('ShopGoods.html',goods=goods.paginate(page,number,False),user_=current_user,bus=bus,
                               collections=Collection.query.all(),col=Collection(title='tovary',trans='Все товары'))

@app.route('/sign',methods=['GET', 'POST']) #регистрация
def sign():
    sign_=request.form.get('login')
    password=request.form.get('password')
    if request.method=='POST':
        if not (sign_ or password):
            flash('Please, fill all fields')
        else:
            if User.query.filter_by(name=sign_).first()==None:
                passw=generate_password_hash(password)
                user=User(name=sign_,password=passw)
                db.session.add(user)
                db.session.commit()
                return redirect('/')
            else:
                flash('User already exists')
    return render_template('ShopSign.html',title='Регистрация',user_=current_user)

@app.route('/logout') #выход из аккаунта
def logout():
    logout_user()
    return redirect(request.referrer)

  if __name__=='__main__':
    app.run(debug=True)
