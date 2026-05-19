document.getElementById(
                'forecastLstChart1'
            ),

            {
                type:'line',

                data:{
                    labels:
                        forecastData1.map(
                            f => f.date
                        ),

                    datasets:[{

                        label:'Time 1',

                        data:
                            forecastData1.map(
                                f => f.lst
                            ),

                        borderColor:'#38bdf8',

                        backgroundColor:
                            'rgba(56,189,248,0.12)',

                        tension:0.4,

                        fill:false,

                        pointRadius:5
                    }]
                },

                options:{
                    responsive:true,

                    maintainAspectRatio:false,

                    plugins:{
                        legend:{
                            display:false
                        }
                    },

                    scales:{
                        y:{
                            min:0,
                            max:50
                        }
                    }
                }
            }
        );
}