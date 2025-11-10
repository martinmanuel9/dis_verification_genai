# Top Level Requests for Test Plan Generation 
The goal is to generate a test plan based on the a standard that has been injested onto the vector database. 

To meet the test plan generation the example we want to replicate is the following:
1. Upload a document like disr_ipv6_50.pdf considered the standard we want to generate a test plan. 
2. Based on the implementation of Document Generator we need to generate a document just like ipv6v4_may09.pdf
    2.1 Use the agent pipeline to generate a test plan. 
    2.1.1 The agent pipeline should have the capability of creating a test plan so that it directly exports something like ipv6v4_may09.pdf
    2.2 Create an evaluation metric to compare the similarities of the document generated in comparison the the ipv6v4. 
3. The test plan that is generated is in the format of disr_ipv6_50.pdf and have the same sections. 