from playwright.sync_api import sync_playwright
import time

def get_cert_loan_links_tuple(date:str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        page.goto("https://sf.citidirect.com/stfin/index.html")
        print(page.title())
        frame = page.locator('#outerframe')
        mbs_button = page.frame('left').locator('a#MBS')
        mbs_button.click()
        time.sleep(10)

        amc_button = page.frame('main').locator('tr:has-text("MBSCitigroup Mortgage Loan Trust Inc2006-AMC1Public") > td:has-text("2006-AMC1") > a')
        amc_button.click()
        time.sleep(10)

        link_locators = page.frame('main').locator(f'a.nodec1bold').all()

        main_link = "https://sf.citidirect.com"
        cert_href = ""
        loan_href = ""
        
        for link in link_locators:
            link_href = link.get_attribute('href')
            if 'CertStmtCMLT06AMC1' + date in link_href:
                cert_href = main_link + link_href
            
            if 'LoanDetailCMLT06AMC1' + date in link_href:
                loan_href = main_link + link_href

        browser.close()

        return cert_href, loan_href

if __name__=='__main__':
    print(get_cert_loan_links_tuple("2309"))
