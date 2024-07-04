let vm = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        username: getCookie('username'),
        order_id: '',
        status: '',
    },
    mounted(){
    },
    methods: {
            oper_btn_click(order_id, status){
                this.order_id = order_id;
                this.status = status;
                let url = '/orders/comment/?order_id=' + order_id
                // axios.get(url,{
                //     responseType: 'json'
                // }).then(response => {
                //     console.log(response.response)
                // }).catch(error => {
                //     console.log(error.response);
                // })
                location.href = url
            }
    }
});