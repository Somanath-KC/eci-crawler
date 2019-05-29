import requests
import scrapy
import re
import json
import os


if('crawler-data' not in os.listdir()):
    os.mkdir('crawler-data')
    os.mkdir(os.path.join('crawler-data','ac'))
elif('ac' not in os.listdir('crawler-data')):
    os.mkdir(os.path.join('crawler-data','ac'))

whole_data = []
states_ac = {}

def fetch_data(state_code='S01' , ac_code="1"):
    url = 'http://results.eci.gov.in/ac/en/constituencywise/Constituencywise'+state_code+ac_code+'.htm'
    return requests.get(url).text

def fetch_states():
    response_data = fetch_data()
    global states_ac
    sel = scrapy.Selector(text=response_data)
    state_code_list = sel.css('html > body > div:nth-of-type(1) > input::attr(id)').extract()
    states_ac_list = sel.css('html > body > div:nth-of-type(1) > input::attr(value)').extract()
    for state in range(len(state_code_list)):
        codes_array = []
        for code in states_ac_list[state].split(";"):
             temp_code = (code.split(",")[0])
             if(len(temp_code) > 0):
                 codes_array.append(temp_code)
        states_ac[state_code_list[state]] = codes_array

def get_state_ac(response_data):
    sel = scrapy.Selector(text=response_data)
    css_path = "table[cellpadding='5'] > tbody > tr:nth-of-type(1) > td::text"
    temp_list = sel.css(css_path).extract()[0].split("-")
    return (re.sub(r"[^a-zA-Z0-9]+", ' ', temp_list[0])[1:], re.sub(r"[^a-zA-Z0-9]+", ' ', temp_list[1])[:-1])

def get_result(response_data):
    return_result = []
    sel = scrapy.Selector(text=response_data)
    css_path = "table[cellpadding='5'] > tbody tr"
    ext_data = sel.css(css_path).extract()
    headers = ["Candidate", "Party", "EVM Votes", "Postal Votes", "Total Votes", "Percentage of Votes"]
    for item in ext_data[3:-1]:
        result_dict = {}
        in_sel = scrapy.Selector(text = item)
        for data in range(2,8):
            data_out = in_sel.xpath('./body/tr/td['+str(data)+']/text()').extract()[0]
            if data > 3 and data < 7:
                result_dict[headers[data-2]] = int(data_out)
            elif data == 7:
                result_dict[headers[data-2]] = float(data_out)
            else:
                result_dict[headers[data-2]] = data_out
        return_result.append(result_dict)
    return return_result[:]

def get_voters(response_data):
    voters_dict = {}
    sel = scrapy.Selector(text=response_data)
    css_path = "table[cellpadding='5'] > tbody tr"
    ext_data = sel.css(css_path).extract()[-1]
    in_sel = scrapy.Selector(text=ext_data)
    voters_dict['EVM Voters'] = int(in_sel.xpath('./body/tr/td[4]/text()').extract()[0])
    voters_dict['Postal Voters'] = int(in_sel.xpath('./body/tr/td[5]/text()').extract()[0])
    voters_dict['Total Voters'] = int(in_sel.xpath('./body/tr/td[6]/text()').extract()[0])
    return voters_dict

def build_json(state_code, ac_code):
    raw_response = fetch_data(state_code, ac_code)
    json_result = {}
    json_state_ac_array = get_state_ac(raw_response)
    print("Scraping data from "+ json_state_ac_array[0]+" : "+json_state_ac_array[1])
    json_result['State'] = json_state_ac_array[0]
    json_result['AC_Name'] = json_state_ac_array[1]
    json_result['AC_Number'] = ac_code
    json_result['Result'] = get_result(raw_response)
    json_result['Voters'] = get_voters(raw_response)
    json_result['Year'] = 2019
    return json_result

def build_results():
    global whole_data
    fetch_states()
    for state in states_ac.keys():
        state_result = []
        print('*********************\n*********************\n*********************\n')
        for ac in states_ac[state]:
            result_dict = build_json(state, ac)
            state_result.append(result_dict)
            whole_data.append(result_dict)
            if(result_dict['State'] not in os.listdir(os.path.join('crawler-data','ac'))):
                print('Creating Directory ---  {}'.format(result_dict['State']))
                os.mkdir(os.path.join('crawler-data','ac',result_dict['State']))
            ac_file = open(os.path.join('crawler-data','ac',result_dict['State'],result_dict['AC_Name']+'.json'),'w')
            ac_file.write(json.dumps(result_dict))
            ac_file.close()
        state_file = open(os.path.join('crawler-data','ac',result_dict['State'],result_dict['State']+'.json'), 'w')
        state_file.write(json.dumps(state_result))
        state_file.close()
    country_file = open(os.path.join('crawler-data','ac','result.json'), 'w')
    country_file.write(json.dumps(whole_data))
    country_file.close()

build_results()