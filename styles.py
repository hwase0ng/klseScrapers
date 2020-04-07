t01 = "<style> \
                    table { \
                      border-collapse:collapse;width:100%; \
                    } \
                    table, th, td { \
                      border: 1px solid black; \
                      border-collapse: collapse; \
                    } \
                    td { \
                      padding: 15px; \
                      text-align: right; \
                    } \
                    table tr:nth-child(even) { \
                      background-color: #F2F2F2; \
                    } \
                    table tr:nth-child(odd) { \
                     background-color: #ffffff; \
                    } \
                    table th { \
                      background-color: #F1F1F1; \
                      color: black; \
                      text-align: center; \
                    } \
                 </style>"

browserref = "<head> \
                <style> \
                    table#t01 { \
                      border-collapse:collapse;width:100%; \
                    } \
                    table#t01 tr:nth-child(even) { \
                       background-color: #F2F2F2; \
                    } \
                    table#t01 th { \
                      text-align:center; \
                      color: black; \
                      height: 44px; \
                      background-repeat:no-repeat; \
                      background-position:center center; \
                      border:1px solid #d4d4d4; \
                      font-weight:bold;color: black;\
                      padding:11px 5px 11px 5px;vertical-align:middle; \
                    } \
                    td { \
                      border:1px solid #d4d4d4; \
                      text-align:right; \
                      padding:8px; \
                      vertical-align:top; \
                    } \
                </style> \
             </head>"

striped = "<head> \
                <style> \
                    table { \
                      border-collapse:collapse;width:100%; \
                    } \
                    tr:nth-child(even) { \
                       background-color: #f2f2f2; \
                    } \
                    th, td { \
                      text-align: left; \
                      padding: 8px; \
                    } \
                </style> \
             </head>"

