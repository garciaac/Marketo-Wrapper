__author__ = "Andrew Garcia <angarcia@marketo.com>"

import time
import httplib2
import json
import logging

class MarketoWrapper:
    """
    This class serves as a wrapper for the Marketo REST API. It is used
    in marketo_connector.py as the interface to a marketo instance.
    
    Attributes:
        __token (string):       The access token to be used to authenticate
                                API calls. 
        __expire_time (float):  When the access token expires and needs to be regenerated.
                                It is checked before every API call
        __http (httplib2.Http): The HTTP object the wraps all of the HTTP functionality required.
        __munchkin (string):    The munchkin ID of the Marketo instance
    """

############################################################################################
#                                                                                          #
#                                   Constructor                                            # 
#                                                                                          #             
############################################################################################

    def __init__(self, munchkin_id, client_id, client_secret):
        """
        The constructor performs all initialization as well as generates
        the first access token. All API calls will double check to make 
        sure the token is still valid before executing.
        
        Args:
            munchkin_id (string):    The munchkin ID of the Marketo instance
            client_id (string):      The client ID of the appropriate API user
            client_secret (string):  The client secret of the appropriate API user
        """
        self.__munchkin = munchkin_id
        # The httplib2.Http constructor takes an optional directory argument
        # where caching will be done. The directory does not need to exist beforehand.
        self.__http = httplib2.Http(".http_cache")
        # This will store credentials in __http so they do not need to be passed
        # each time a token is requested.
        self.__http.add_credentials(client_id, client_secret)
        # This value will be overwritten by _getAccessToken, so it is just
        # used for initialization
        self.__expire_time = 0
        self.__token = self.__generateAccessToken(self.__munchkin)
        
############################################################################################
#                                                                                          #
#                                   Private Methods                                        # 
#                                                                                          #             
############################################################################################
    
    def __generateAccessToken(self, munchkin_id):
        """
        This method requests a new access token from the REST API identity endpoint
        
        Note:
            The client ID and secret required to generate the token were added to the 
            __http attribute in the class constructor, so if the server requires authentication
            (it does), the httplib2 module does the credential handling automatically.
        
        Args:
            None
            
        Returns:
            string: The access token given by the server
        """
        # Request the token
        response, content = self.__http.request("https://"+self.__munchkin+
                                               ".mktorest.com/identity/"+
                                               "oauth/token?grant_type=client_credentials")
        # If the request was successful, return the token.
        if (response.status == 200):
            content = json.loads(content.decode("utf-8"))
            self.__reset_expire_time(content["expires_in"])
            return content["access_token"]
        else:
            print(str(response.status)+"\n"+response.reason)

    def __generic_api_call(self, call, method, payload, headers):
        """
        This method executes a generic API call to the REST API endpoint. The correct syntax
        should be passed into this method from inside of each call wrapper. 
        
        Args:
            call (string):       The actual API call to make. This method contains the endpoint itself,
                                 but the desired call must be given from outside.
            method (string):     The HTTP method to use (GET, POST, PUT etc.).
            payload_ (string):   Any payload that should be sent to the server.
            headers_ (dict):     Any custom headers to send. The access token is added automatically
                                 inside the method, so it does not need to be added manually from outside.
        """
        # Check to see if the token has expired. If so, generate a new one.
        if self.__expire_time < time.time():
            self.__token = self.__generateAccessToken(self.__munchkin)
        
        # Add the access token to the HTTP header. 
        headers["authorization"] = "Bearer "+self.__token
        # Prevents mismatch errors by exlicitly requesting json
        headers["content-type"] =  "application/json"
        
        print(json.dumps(headers))
        
        # Make the API call. Make sure to use json.dumps() on the payload since httplib2 does
        # not automatically serialize the data.
        response, content = self.__http.request("https://"+self.__munchkin+".mktorest.com/"+
                                               call, method, headers, payload)
        
        # If the call was successful, return the content retrieved from the server.
        if (response.status == 200):
            print("successful")
            return content
        else:
            raise Exception(str(response.status)+"\n"+response.reason)
    
    def __reset_expire_time(self, expiresIn):
        """
        This method is used to reset the clock on an access token. When a new token is 
        generated, this method should be called with the "expires_in" field of the
        response from the Marketo identity endpoint. 
        
        Args:
            expiresIn (int):    The number of seconds until the new token expires. It should
                                be retrieved from the response of the Marketo identity endpoint
        """
        self.__expire_time = time.time() + expiresIn

############################################################################################
#                                                                                          #
#                                      API Calls                                           # 
#                                                                                          #             
############################################################################################
    
    def create_update_leads(self, leads):
        """
        This method makes the create_update_leads call.
        
        Args:
            leads (list):   A list of dicts containing all of the leads to upload
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/v1/leads.json"
        method = "POST"
        payload = {"input": leads}
        return self.__generic_api_call(call, method, payload, {})
        
    def merge_lead(self, winner, loser):
        """
        This method makes the merge_lead call.
        
        Args:
            winner (string):    The lead id of the authoritative lead
            losers (list):      A list of strings containing all of the lead ids to 
                                merge, but will yield to winner for conflicting values
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/v1/leads/"+leadID+"/merge.json"
        method = "POST"
        return self.__generic_api_call(call, method, {}, {})
    
    def get_lead_by_id(self, lead):
        """
        This method makes the get_lead_by_id call.
        
        Args:
            lead (string):   The id of the lead needed
            
        Returns:
            dict:   The response from the server
        """
        call = "/rest/v1/lead/"+lead+".json"
        method = "GET"
        return self.__generic_api_call(call, method, {}, {})
    
    def get_email_by_id(self, email):
        """
        This method gets an email asset given its id
        
        Args:
            email (string): The id of the desired email asset
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/email/"+email+".json"
        method = "GET"
        return self.__generic_api_call(call, method, {}, {})
    
    
    # This doesn't work
    def create_email_template(self, name, folder):
        """
        This method creates an email template from an HTML file
        
        Args:
            name (string):      The desired name of the email template
            folder (int):       The integer id of the folder in Marketo. It can
                                be obtained via the folder API calls.
            template (string):  The filepath of the HTML file.
        Returns:
            dict:   The response from the server
        """
        print("inside function\n\n")
        content = open("""C:/Users/angarcia/Box Sync/Documents/_Dev/Asset API Tests/Email_Nurture_program_Email_Nurture_2 (1).html""").read()
        
        call = "rest/asset/v1/emailTemplates.json"
        method = "POST"
        headers = {}
        payload = {}
        headers["name"] = name
        headers["folder"] = folder
        payload["content"] = content
        return self.__generic_api_call(call, method, payload, headers)
    
if __name__ == "__main__":
    logging.basicConfig(filename="logs.log", filemode="w", level=logging.DEBUG)
    munchkin = "679-WJZ-355"
    client_id = "a4e379b7-b139-49c6-a2e6-aa485f15ef16"
    client_secret = "A7nXl10KIuz5TXTTtddZoTskszNwMfPR"
    marketo = MarketoWrapper(munchkin, client_id, client_secret)
        
    print(marketo.create_email_template("api-email-template", "14"))
        