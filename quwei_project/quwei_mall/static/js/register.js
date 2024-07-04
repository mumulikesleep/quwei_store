let vm = new Vue({
    el: '#app', //通过id选择器进行绑定html内容
        //修改vue读取变量的语法
    delimiters: ['[[',']]'],
    data: {     //数据对象
        send_flag: false,   //防止恶意发送邮箱验证码的唯一标识
        //v-model
        username: '',
        password: '',
        password2: '',
        mobile: '',
        allow: '',
        image_code: '',
        sms_code: '',
        //v-bind
        image_code_url: '',
        uuid: '',
        //v-show
        error_name: false,
        error_password: false,
        error_password2: false,
        error_mobile: false,
        error_allow: false,
        error_image_code: false,
        error_sms_code: false,
        //error_message
        error_name_message: '',
        error_mobile_message: '',
        error_image_code_message: '',
        sms_code_tip: '获取邮箱验证码',
        error_sms_code_message: '',
    },
    mounted(){//页面加载完成会被调用
        //生成图形验证码
        this.generate_image_code();
    },
    methods:{//定义和实现事件的方法
        //发送邮箱验证码
        send_sms_code(){
            //避免用户恶意频繁地点击获取邮箱验证码的标签
            if (this.send_flag == true) {
                console.log(1)
                return;
            }
            this.send_flag = true;
            //校验图片验证码格式和邮箱格式与重复注册
            this.check_image_code();
            this.check_mobile();
            if (this.error_mobile == true || this.error_image_code == true) {
                this.send_flag = false;
                return;
            }
            let url = '/sms_codes/' + this.mobile + '/?image_code=' + this.image_code +'&uuid=' + this.uuid;
            axios.get(url,{
                responseType: 'json',
            }).then(response => {
                if (response.data.code == '0'){
                    //展示倒计时60秒效果
                    let num = 60;
                    let t = setInterval(() => {
                        if (num == 1) {//倒计时即将结束
                            clearInterval(t);//停止定时器
                            this.sms_code_tip = '获取邮箱验证码';//还原sms_code_tip
                            this.send_flag = false;
                            this.generate_image_code();//重新生成图形验证码
                        }else {
                            num -= 1;
                            this.sms_code_tip = num + '秒';
                        }
                    },1000)
                }else {
                    if (response.data.code == '4001'){//图形验证码错误
                        this.error_image_code_message = response.data.errmsg;
                        this.error_image_code = true;
                    }else {//4002 邮箱验证码错误
                        this.error_sms_code_message = response.data.errmsg;
                        this.error_sms_code = true;
                    }
                    this.send_flag = false;
                    this.generate_image_code()
                }
            }).catch(error => {
                console.log(error.response);
                this.send_flag = false;
            })
        },
        //生成图形验证码的方法：封装的思想，代码的复用
        generate_image_code(){
            this.uuid = generateUUID();//generateUUID是提供的生成uuid的代码
            this.image_code_url = '/image_codes/' + this.uuid + '/';
        },
        //校验用户名
        check_username(){
            let re = /^[a-zA-Z0-9_-]{5,20}$/;
            if (re.test(this.username)){
                this.error_name = false;
            }else {
                this.error_name_message = '请输入5-20个字符的用户名';
                this.error_name = true;
            }
            //判断用户名是否重复注册(ajax请求)
            if (this.error_name == false){//只有当用户输入的用户名满足条件时才会判断
                let url = '/usernames/' + this.username + '/count/';
                axios.get(url,{
                    responseType: 'json'
                }).then(response => {
                    if (response.data.count == 1){
                        //用户名已存在
                        this.error_name_message = '用户名已存在';
                        this.error_name = true;
                    }else {
                        //用户名不存在
                        this.error_name = false;
                    }
                }).catch(error => {
                    console.log(error.response);
                })
            }
        },
        //校验密码
        check_password(){
            let re = /^[a-zA-Z0-9]{8,20}$/;
            if (re.test(this.password)){
                this.error_password = false;
            }else {
                this.error_password = true;
            }
        },
        // 校验确认密码
        check_password2(){
            if (this.password != this.password2){
                this.error_password2 = true;
            } else {
                this.error_password2 = false;
            }
        },
        check_image_code(){
            if (this.image_code.length != 4){
                this.error_image_code = true;
                this.error_image_code_message = '请输入图形验证码';
            }else {
                this.error_image_code = false;
            }
        },
        // 校验邮箱
        check_mobile(){
            let re = /^[1-9][0-9]{4,}@qq.com$/;
            if(re.test(this.mobile)) {
                this.error_mobile = false;
            } else {
                this.error_mobile_message = '您输入的邮箱格式不正确';
                this.error_mobile = true;
            }
            //判断邮箱是否重复注册(ajax请求)
            if (this.error_mobile == false){//只有当邮箱正确时才会判断
                let url = '/mobiles/' + this.mobile + '/count/';
                axios.get(url,{
                    responseType: 'json'
                }).then(response => {
                    if (response.data.count == 1){
                        this.error_mobile_message = '邮箱已被注册';
                        this.error_mobile = true;
                    }else {
                        this.error_mobile = false;
                    }
                }).catch(error => {
                    console.log(error.response)
                })
            }
        },
        //校验邮箱验证码
        check_sms_code(){
            if (this.sms_code.length != 6) {
                this.error_sms_code = true;
                this.error_sms_code_message = '请输入邮箱验证码';
            }else {
                this.error_sms_code =false;
            }
        },
        // 校验是否勾选协议
        check_allow(){
            if(!this.allow) {
                this.error_allow = true;
            } else {
                this.error_allow = false;
            }
        },
        // 监听表单提交事件
        on_submit(){
            //这五个是判断参数是否齐全
            this.check_username();
            this.check_password();
            this.check_password2();
            this.check_mobile();
            this.check_sms_code();
            this.check_allow();

            if(this.error_name == true || this.error_password == true || this.error_password2 == true
                || this.error_mobile == true || this.error_sms_code == true || this.error_allow == true) {
                // 禁用表单的提交
                // window.event.returnValue = false;    老方法
                event.preventDefault(); //新方法
        }
        },
    }
});