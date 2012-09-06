'''
Created on Jul 3, 2012

@author: yaqin276
'''
from feat2tree_v5 import *
import re,sys,os
from optparse import OptionParser
from xml.etree.ElementTree import Element, SubElement, ElementTree, parse
import nltk.corpus.reader.propbank
import subprocess
#from pylab import *
#import matplotlib.pyplot as plt

#from mpl_toolkits.mplot3d import axes3d
import numpy as np

class morphology(object):
    def __init__(self):
        '''
        Constructor
        '''
        self.surf = ""
        self.lex = ""
        self.synt = ""
        self.number = []
        self.deriv= defaultdict()
        self.person = []
        self.tense = []
        self.grade = []
    def getRule(self,cur_morph):
        '''
        given the morphology of a term, generate morphology rules
        '''
        rule_list = {}
        noun_plural = {}
        verb_norm = {}
        verb_person = {}
        verb_tense = {}
        verb_tense_person = {}
        verb_er = {}
        base_pos = {}
        pos_map = {"s-adv":"RB","s-aux":"MD","s-coord-conj":"CC","s-demonstr-adj":"DT","s-determiner-adj":"DT","s-gen-particle":"POS","s-indef-art":"DT","s-prep":"IN","s-adv-particle":"RP"}


        syn_state = []
        if cur_morph.synt in pos_map:
            rule_temp = ""
            rule_temp = "q"+pos_map[cur_morph.synt].lower()+"."+cur_morph.lex+" -> "+pos_map[cur_morph.synt]+"("+cur_morph.lex+")"
            if rule_temp not in base_pos:
                base_pos[rule_temp] = 0
            
        if cur_morph.synt in "s-adj".split():
            qstate = ""
            rule_temp = ""
            if"COMPARATIVE".lower() in cur_morph.grade:
                qstate = "JJR"
            elif "SUPERLATIVE".lower() in cur_morph.grade:
                qstate = "JJS"
            else:
                qstate = "JJ"
            rule_temp = "q"+qstate.lower()+"."+cur_morph.surf+" -> "+qstate+"("+cur_morph.surf+")"
            if qstate != "" and rule_temp not in base_pos:
                base_pos[rule_temp] = 0           
        
        '''
        number rules
        '''       
        if re.search("noun", cur_morph.synt.lower()):
            '''
            rules for plural noun lexicon
            '''
            
            for s in cur_morph.number:
                rule_temp = ""
                if re.search("sing",s.lower()):
                    a_syn_state = "qnn."
                    rule_temp = a_syn_state+cur_morph.lex+" -> NN("+cur_morph.surf+")"
                        
                if re.search("plural",s.lower()):
                    a_syn_state = "qnns."
                    rule_temp = a_syn_state+cur_morph.lex+" -> NNS("+cur_morph.surf+")"

                if rule_temp != "" and rule_temp not in rule_list:
                    rule_list[rule_temp] = 0
                if rule_temp != "" and rule_temp not in noun_plural:
                    noun_plural[rule_temp] = 0
        
        if re.search("verb", cur_morph.synt.lower()):
            '''
            rules for normalization of verbs
            rules for personalization of verbs -- accuse -> accuser
            '''
         
            
            for d in cur_morph.deriv:
                rule_temp = ""
                all_d = d.lower().split("-")
                if "actor" in all_d and "noun" in all_d:
                    a_syn_state = "qnp.(/ person :ARG0-of (/ "
                    for ad in cur_morph.deriv[d]:
                        rule_temp = a_syn_state+cur_morph.lex+"-01)) -> qnp.(/ "+ad+")"
                        if rule_temp not in verb_er:
                            verb_er[rule_temp] = 0
                        if rule_temp != "" and rule_temp not in rule_list:
                            rule_list[rule_temp] = 0
                            
                elif len(all_d) == 1 and "noun" in all_d:
                    a_syn_state = "qnn."
                    for ad in cur_morph.deriv[d]:
                        rule_temp = a_syn_state+cur_morph.lex+"-01 -> qnp.(/ "+ad+")"
                        if rule_temp not in verb_er:
                            verb_norm[rule_temp] = 0                    
                        if rule_temp != "" and rule_temp not in rule_list:
                            rule_list[rule_temp] = 0

            
            '''
            rules for verb+ third person
            F-THIRD-P  F-SECOND-P  F-FIRST-P
            '''
            
            for p in cur_morph.person:
                rule_temp = ""
                vbp_rule = ""
                if re.search("third",p.lower()):
                    b_syn_state = "qvbz."
                    rule_temp = b_syn_state+cur_morph.lex+"-01 -> VBZ("+cur_morph.surf+")"                
                elif re.search("first",p.lower()):
                    b_syn_state = "qvb."
                    rule_temp = b_syn_state+cur_morph.lex+"-01 -> VB("+cur_morph.surf+")"  
                    vbp_rule =  "qvbp." +cur_morph.lex+"-01 -> VBP("+cur_morph.surf+")"  
                if rule_temp != "" and rule_temp not in rule_list:
                    rule_list[rule_temp] = 0
                if rule_temp != "" and rule_temp not in verb_person:
                    verb_person[rule_temp] = 0    
                if rule_temp != "" and rule_temp not in verb_tense_person:
                    verb_tense_person[rule_temp] = 0
                    verb_tense_person[vbp_rule] = 0
                    
            '''
            rules for verb+tense
            F-PRES-TENSE  F-PAST-PART  F-PRES-PART  F-PAST-TENSE  F-PRES-IN
            '''  
            
            for p in cur_morph.tense:
                rule_temp = []
                if re.search("past\-tense",p.lower()):
                    b_syn_state = "qvbd."
                    rule_temp.append(b_syn_state+cur_morph.lex+"-01 -> VBD("+cur_morph.surf+")")
                              
                elif re.search("past\-part",p.lower()):
                    b_syn_state = "qvbn."
                    rule_temp.append(b_syn_state+cur_morph.lex+"-01 -> VBN("+cur_morph.surf+")")
                    
                elif re.search("pres\-part",p.lower()):
                    b_syn_state = "qvbg."
                    rule_temp.append(b_syn_state+cur_morph.lex+"-01 -> VBG("+cur_morph.surf+")")
                
                for a_rule in rule_temp:
                    if a_rule not in rule_list:
                        rule_list[a_rule] = 0
                for a_rule in rule_temp:
                    if a_rule not in verb_tense:
                        verb_tense[a_rule] = 0      
                for a_rule in rule_temp:
                    if a_rule not in verb_tense_person:
                        verb_tense_person[a_rule] = 0          

        return [verb_tense,verb_person,noun_plural,verb_norm,verb_er,rule_list,verb_tense_person,base_pos]
        
        
       # rule_list.append("qnp."+cur_morph.lex+" -> NP(CD("+new_cd+") NN(million))")
    def jjtorb(self,jj):
        '''
        convert jj to rb
        '''
        rb = ""
        if re.match(".*y$",jj):
            rb = jj[:-1]+"ily"
        elif re.match(".*ic$",jj):
            rb = jj +"ally"
        elif len(jj) >=3 and re.match("[^aeiou]",jj[-3]) and re.match(".*le$",jj):
            rb = jj[:-1] +"y"
        else:
            rb = jj+"ly"
        return rb
        
    def jjToNegjj(self,jj):
        '''
        convert positive jj to negative jj
        '''    
        njj = []
        for prefix in "un im in il ir dis non".split():
            njj.append(prefix+jj)
        return njj
        

    def generateMorphRules(self,morph_file,output):    
        input_file = open(morph_file, "r")
        output_file = open(output, "w")
        noun_plural_output_file = open(output+".nnpl.txt", "w")
        verb_norm_output_file = open(output+".vnor.txt", "w")
        verb_er_output_file = open(output+".ver.txt","w")
        verb_psn_output_file = open(output+".vpsn.txt", "w")
        verb_ten_output_file = open(output+".vten.txt", "w")
        verb_ten_psn_output_file = open(output+".vtenpsn.txt", "w")
        jjrb_output_file = open(output+".jjrb.txt", "w")
        jjnjj_output_file = open(output+".jjnjj.txt", "w")
        jjnrb_output_file = open(output+".jjnrb.txt", "w")
        base_pos_output_file = open(output + ".basepos.txt","w")
        mdict = {}
        valid_item = True
        all_rules = {}
        all_noun_plural = {}
        all_verb_norm = {}
        all_verb_er = {}
        all_verb_psn = {}
        all_verb_ten = {}
        all_jj_rb = {}
        all_jj_njj = {}
        all_jj_nrb = {}
        all_jj = defaultdict()
        all_rb = defaultdict()
        all_tense_person={}
        all_base_pos = {}
        for line in input_file:
            cur_morph = morphology()
            if not re.match("::",line):
                continue
            #print line
            for i in re.finditer(r'::?(?P<key>[^" ]+) (?P<v>":@"|":"|[^:]+)',line):
                category = i.groupdict()["key"]
                value = i.groupdict()["v"]
                if category.lower() == "surf":
                    cur_morph.surf = value.strip().strip('"').lower()
                    if len(cur_morph.surf.split()) >1:
                        valid_item = False
                elif category.lower() == "lex":
                    cur_morph.lex = value.strip().strip('"').lower()
                    if len(cur_morph.lex.split()) >1:
                        valid_item = False
                elif category.lower() == "synt":
                    cur_morph.synt = value.strip().lower()
                elif category.lower() == "number":
                    cur_morph.number.append(value)   
                elif re.search("deriv",category.lower()):
                    dpos = "-".join(category.lower().split("-")[1:])
                    if dpos not in cur_morph.deriv:
                        cur_morph.deriv[dpos] = [value.strip().strip('"').lower()]
                    else:
                        cur_morph.deriv[dpos].append(value.strip().strip('"').lower())
                elif re.search("person",category.lower()):
                    cur_morph.person.append(value)
                elif re.search("tense", category.lower()):
                    cur_morph.tense.append(value)
                elif re.match("grade",category.lower()):
                    cur_morph.grade.append(value.strip().lower())
                if category not in mdict:
                    mdict[category]={value:0}
                else:
                    mdict[category][value] = 0
                    
            if re.match("s-adj",cur_morph.synt) and "ungraded" in cur_morph.grade:
                all_jj[cur_morph.surf] = 0
            if re.match("s-adv",cur_morph.synt):
                all_rb[cur_morph.surf] = 0
            
            if valid_item:
                verb_tense,verb_person,noun_plural,verb_norm,verb_er,rule_list,verb_tense_person,base_pos = self.getRule(cur_morph)
                
            
            for a_rule in rule_list:
                if a_rule not in all_rules:
                    all_rules[a_rule] = 0
                    
            for a_rule in noun_plural:
            
                if a_rule not in all_noun_plural:
                    all_noun_plural[a_rule] = 0   

            for a_rule in verb_norm:
                if a_rule not in all_verb_norm:
                    all_verb_norm[a_rule] = 0   

            for a_rule in verb_er:
                if a_rule not in all_verb_er:
                    all_verb_er[a_rule] = 0   

            for a_rule in verb_person:
                if a_rule not in all_verb_psn:
                    all_verb_psn[a_rule] = 0   

            for a_rule in verb_tense:
                if a_rule not in all_verb_ten:
                    all_verb_ten[a_rule] = 0   

            for a_rule in verb_tense_person:
                if a_rule not in all_tense_person:
                    all_tense_person[a_rule] = 0   

            for a_rule in base_pos:
                if a_rule not in all_base_pos:
                    all_base_pos[a_rule] = 0   
                            
            valid_item = True

        '''
        generate rules
        if ulf's dictionary can't stem -ly adverbs to adjective form, then you can take every adjective X, apply the following rule:
        http://literacy.kent.edu/Midwest/Materials/ndakota/spelling/lesson7.html
        then check if the resulting adverb Y is a word that exists somewhere in ulf's list.
        if it's there, then it's 99% sure you can safely add this to the NLG system:
        qrb.X -> RB(Y)
        '''
        for a_jj in all_jj:
            a_rb = self.jjtorb(a_jj)
            if a_rb in all_rb:
                jj_rule = "qrb."+a_jj+" -> RB("+a_rb+")"
                if jj_rule not in all_jj_rb:
                    all_jj_rb[jj_rule] = 0
                    
            neg_jj_list = self.jjToNegjj(a_jj)
            for a_neg_jj in neg_jj_list:
                if a_neg_jj in all_jj:
                    njj_rule = "qjj.(/ "+a_jj+" :polarity -) -> JJ("+a_neg_jj+")"
                    if njj_rule not in all_jj_njj:
                        all_jj_njj[njj_rule] = 0
                    
                    a_neg_rb = self.jjtorb(a_neg_jj)
                    if a_neg_rb in all_rb:
                        nrb_rule = "qrb.(/ "+a_jj+" :polarity -) -> RB("+a_neg_rb+")"
                        if nrb_rule not in all_jj_nrb:
                            all_jj_nrb[nrb_rule] = 0
                        
            

        for a_rule in sorted(all_base_pos.iterkeys()):
            base_pos_output_file.write(a_rule+"\n")
            
        for a_rule in sorted(all_noun_plural.iterkeys()):
            noun_plural_output_file.write(a_rule+"\n")
            
        for a_rule in sorted(all_verb_norm.iterkeys()):
            verb_norm_output_file.write(a_rule+"\n")
            
        for a_rule in sorted(all_verb_er.iterkeys()):
            verb_er_output_file.write(a_rule+"\n")
           
        for a_rule in sorted(all_verb_psn.iterkeys()):
            verb_psn_output_file.write(a_rule+"\n")          

        for a_rule in sorted(all_verb_ten.iterkeys()):
            verb_ten_output_file.write(a_rule+"\n")        
            
        for a_rule in sorted(all_jj_rb.iterkeys()):
            jjrb_output_file.write(a_rule+"\n")    
            
        for a_rule in sorted(all_jj_njj.iterkeys()):
            jjnjj_output_file.write(a_rule+"\n")          

        for a_rule in sorted(all_jj_nrb.iterkeys()):
            jjnrb_output_file.write(a_rule+"\n")   

        for a_rule in sorted(all_tense_person.iterkeys()):
            verb_ten_psn_output_file.write(a_rule+"\n")  

        jjrb_output_file.close()
        jjnjj_output_file.close()
        jjnrb_output_file.close()
        verb_ten_output_file.close()
        verb_psn_output_file.close()
        noun_plural_output_file.close()
        verb_norm_output_file.close()
        verb_er_output_file.close()
        output_file.close()
        verb_ten_psn_output_file.close()
        base_pos_output_file.close()
        
        for m in mdict:
            if m in ["NUMBER","PERSON","GENDER","TENSE","SYNT"]:
                print "+++++++++++++++++++++++++++++"
                print m                    
                for k in sorted(mdict[m].keys()):
                    print k,
                print 

class Tuning(object):
    def __init__(self):
        '''
        Constructor
        '''
    def MERTexc(self,default_set,dev_test,base_dir):
#        kbest_file = "/auto/nlg-01/yy_140/generation/dev/lfw-3/dev_20120712.all.cdec.1000-best.txt"
        
        bleu_script="/home/nlg-01/yanggao/sembmt/amr-gen-2012-summer/amr-gen-scripts/multi-bleu.perl"
        
        if dev_test == "train":
            kbest_surfix = "_20120712.50.all.cdec.1000-best.txt"
            ref="/home/nlg-01/yanggao/sembmt/amr-gen-2012-summer/data/wsj100-sent-20120712/train_20120712_reference.50.txt"
            
        else:
            kbest_surfix = "_20120712.all.cdec.1000-best.txt"
            ref="/home/nlg-01/yanggao/sembmt/amr-gen-2012-summer/data/wsj100-sent-20120712/"+dev_test+"_20120712_reference.txt"
        kbest_file = base_dir+"/"+dev_test+"/lfw"+str(default_set)+"/"+dev_test+kbest_surfix
        for lfw in range(-10,11):
            lfw_dir = base_dir+"/"+dev_test+"/mertlfw"+str(default_set)+"_"+str(lfw)
            new_onebest=lfw_dir+"/"+dev_test+"newonebest.txt"
            new_blue=lfw_dir+"/"+dev_test+"newbleu.txt"
            print lfw,
            print """ssh hpc "nohup mkdir %s; cp %s %s; \
            sed 's/ ||| /\\t/g' %s | awk -F '\\t' '{split(\$3,array,\\\" \\\");split(array[1],lm,\\\"=\\\"); split(array[2],lfw,\\\"=\\\");\$4=lm[2]+%s*lfw[2];print \$1\\\" ||| \\\"\$2\\\" ||| \\\"\$3\\\" ||| \\\"\$4}' |\
             sed 's/ ||| /\\t/g' |\
              sort -t $'\\t' -nk 1 -k 4 -r |\
               awk 'BEGIN {a=-999} {if (\$1!=a) {print \$0; a=\$1}}' | sort -t $'\\t' -nk 1 | cut -f 2,2> %s; \
               %s -lc %s < %s > %s\
                                     " """\
                                       %(lfw_dir,kbest_file,lfw_dir,\
                                         lfw_dir+"/"+dev_test+kbest_surfix,lfw,new_onebest,\
                                         bleu_script,ref,new_onebest,new_blue)
            process = subprocess.Popen("""ssh hpc "nohup mkdir %s; cp %s %s; \
            sed 's/ ||| /\\t/g' %s | awk -F '\\t' '{split(\$3,array,\\\" \\\");split(array[1],lm,\\\"=\\\"); split(array[2],lfw,\\\"=\\\");\$4=lm[2]+%s*lfw[2];print \$1\\\" ||| \\\"\$2\\\" ||| \\\"\$3\\\" ||| \\\"\$4}' |\
             sed 's/ ||| /\\t/g' |\
              sort -t $'\\t' -nk 1 -k 4 -r |\
               awk 'BEGIN {a=-999} {if (\$1!=a) {print \$0; a=\$1}}' | sort -t $'\\t' -nk 1 | cut -f 2,2> %s; \
               %s -lc %s < %s > %s\
                                     " """\
                                       %(lfw_dir,kbest_file,lfw_dir,\
                                         lfw_dir+"/"+dev_test+kbest_surfix,lfw,new_onebest,\
                                         bleu_script,ref,new_onebest,new_blue),
                                         shell=True)
            
            process.communicate()       
            
        
        
        
    def lineSearch(self,dev_test,base_dir,pipeline_dir,best_weights):
        '''
        set LFW with different values, run NLG system, and get bleu score and bp
        '''
        #feat_name, lower_value, upper_value
        #pipline = "/home/nlg-01/yanggao/sembmt/amr-gen-2012-summer/amr-gen-scripts/e2e.sh"
        home_dir=base_dir+"/"+dev_test+"/"
        config_file = pipeline_dir+"/"+"e2e.config"
        pipeline = pipeline_dir+"/"+"e2e.sh"
        weight_file = "weights.txt"
        nbest = 1000
        tune_nbest = "tune_"+str(nbest)+"best.txt"
        one_best="onebest.txt"
        
        

        for lfw in range(-10,11):
            
            lfw_dir = home_dir+"lfw"+str(lfw)
            lfw_cdir=re.sub("/","\\/",lfw_dir)
            "LanguageModel 0 WordPenalty 0 DerivSize 0"
            '''
            this is for old pipeline, in which feature weights are written in e2e.config file
            '''
#            process = subprocess.Popen("ssh hpc \"mkdir %s; cp %s %s; sed -i 's/LFW=[-+]\?[0-9]*\.\?[0-9]*/LFW=%s/' %s; sed -i 's/EXP_DIR=.*/EXP_DIR=%s/' %s; nohup %s %s\""\
#                                       %(lfw_dir,config_file,lfw_dir,lfw,lfw_dir+"/e2e.config",lfw_cdir,lfw_dir+"/e2e.config",pipeline,lfw_dir+"/e2e.config"), 
#                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)     
            '''
            this is for tuning pipeline, which takes a weight-file as argument
            '''
            if best_weights == "":
                lm = "1.0"
                wp = str(lfw)
                ds = "0.0"
            else:
                lm, wp, ds = best_weights.split("|")
                lfw_dir = home_dir+"lfw"+str(wp)+"_"+str(ds)
                lfw_cdir=re.sub("/","\\/",lfw_dir)
            print lm, wp, ds

#            "KBEST_CDEC=%d TUNE_KBEST_FILE=%s OUT_CDEC_ONEBEST=run-%.2d-out WEIGHT_FILE=%s %s %s" %($NBEST, $WORKDIR/run$I.nbest, 100, $WEIGHTS, $DECODER, config_file)
#            print """ssh hpc "mkdir %s; cp %s %s; \
#            sed -i 's/EXP_DIR=.*/EXP_DIR=%s/' %s; \
#            echo %s | awk '{print \\\"LanguageModel\\\",\$1\\\"\\nWordPenalty\\\",\$2\\\"\\nDerivSize\\\",\$3}'>%s; \
#            nohup KBEST_CDEC=%s TUNE_KBEST_FILE=%s OUT_CDEC_ONEBEST=%s WEIGHT_FILE=%s %s %s" """\
#                                       %(lfw_dir,config_file,lfw_dir,lfw_cdir,lfw_dir+"/e2e.config",\
#                                         " ".join([lm,wp,ds]),lfw_dir+"/"+weight_file,\
#                                         nbest,lfw_dir+"/"+tune_nbest,lfw_dir+"/"+one_best,lfw_dir+"/"+weight_file,pipeline,lfw_dir+"/e2e.config")


            print """ssh hpc "mkdir %s; cp %s %s; \
                sed -i 's/EXP_DIR=.*/EXP_DIR=%s/' %s; \
                sed -i 's/RAW_INPUT=.*/RAW_INPUT=\$DATA_DIR\/wsj100\-sent\-20120712\/%s_20120712.50.txt/' %s; \
                sed -i 's/REF=.*/REF=\$DATA_DIR\/wsj100\-sent\-20120712\/%s_20120712_reference.50.txt/' %s; \
                echo %s | awk '{print \\\"LanguageModel\\\",\$1\\\"\\nWordPenalty\\\",\$2\\\"\\nDerivSize\\\",\$3}'>%s; \
                KBEST_CDEC=%s TUNE_KBEST_FILE=%s OUT_CDEC_ONEBEST=%s WEIGHT_FILE=%s %s %s" """\
                                           %(lfw_dir,config_file,lfw_dir,lfw_cdir,lfw_dir+"/e2e.config",dev_test,lfw_dir+"/e2e.config",dev_test,lfw_dir+"/e2e.config",\
                                             " ".join([lm,wp,ds]),lfw_dir+"/"+weight_file,\
                                             nbest,lfw_dir+"/"+tune_nbest,lfw_dir+"/"+one_best,lfw_dir+"/"+weight_file,pipeline,lfw_dir+"/e2e.config")

            if dev_test == "train":
                process = subprocess.Popen("""ssh hpc "mkdir %s; cp %s %s; \
                sed -i 's/EXP_DIR=.*/EXP_DIR=%s/' %s; \
                sed -i 's/RAW_INPUT=.*/RAW_INPUT=\$DATA_DIR\/wsj100\-sent\-20120712\/%s_20120712.50.txt/' %s; \
                sed -i 's/REF=.*/REF=\$DATA_DIR\/wsj100\-sent\-20120712\/%s_20120712_reference.50.txt/' %s; \
                echo %s | awk '{print \\\"LanguageModel\\\",\$1\\\"\\nWordPenalty\\\",\$2\\\"\\nDerivSize\\\",\$3}'>%s; \
                KBEST_CDEC=%s TUNE_KBEST_FILE=%s OUT_CDEC_ONEBEST=%s WEIGHT_FILE=%s %s %s" """\
                                           %(lfw_dir,config_file,lfw_dir,lfw_cdir,lfw_dir+"/e2e.config",dev_test,lfw_dir+"/e2e.config",dev_test,lfw_dir+"/e2e.config",\
                                             " ".join([lm,wp,ds]),lfw_dir+"/"+weight_file,\
                                             nbest,lfw_dir+"/"+tune_nbest,lfw_dir+"/"+one_best,lfw_dir+"/"+weight_file,pipeline,lfw_dir+"/e2e.config"), 
                                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)    
            else:
                process = subprocess.Popen("""ssh hpc "mkdir %s; cp %s %s; \
                sed -i 's/EXP_DIR=.*/EXP_DIR=%s/' %s; \
                sed -i 's/RAW_INPUT=.*/RAW_INPUT=\$DATA_DIR\/wsj100\-sent\-20120712\/%s_20120712.txt/' %s; \
                sed -i 's/REF=.*/REF=\$DATA_DIR\/wsj100\-sent\-20120712\/%s_20120712_reference.txt/' %s; \
                echo %s | awk '{print \\\"LanguageModel\\\",\$1\\\"\\nWordPenalty\\\",\$2\\\"\\nDerivSize\\\",\$3}'>%s; \
                KBEST_CDEC=%s TUNE_KBEST_FILE=%s OUT_CDEC_ONEBEST=%s WEIGHT_FILE=%s %s %s" """\
                                           %(lfw_dir,config_file,lfw_dir,lfw_cdir,lfw_dir+"/e2e.config",dev_test,lfw_dir+"/e2e.config",dev_test,lfw_dir+"/e2e.config",\
                                             " ".join([lm,wp,ds]),lfw_dir+"/"+weight_file,\
                                             nbest,lfw_dir+"/"+tune_nbest,lfw_dir+"/"+one_best,lfw_dir+"/"+weight_file,pipeline,lfw_dir+"/e2e.config"), 
                                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)                    
            process.communicate()
            if best_weights != "":
                break
            
    def gridSearch(self,dev_test,base_dir,pipeline_dir,best_weights):
        '''
        set LFW and DS with different values, run NLP system
        '''
        #pipline = "/home/nlg-01/yanggao/sembmt/amr-gen-2012-summer/amr-gen-scripts/e2e.sh"
        home_dir=base_dir+"/"+dev_test+"/"
        config_file = pipeline_dir+"/"+"e2e.config"
        pipeline = pipeline_dir+"/"+"e2e.sh"
        
        weight_file = "weights.txt"
        nbest = 1000
        tune_nbest = "tune_"+str(nbest)+"best.txt"
        one_best="onebest.txt"
        
        
        for lfw in [-1,1,2,3,4,5,9,10]:
            for dsw in range(-10,11):

                lfw_ds_dir = home_dir+"lfw_ds_"+str(lfw)+"_"+str(dsw)
                lfw_ds_cdir=re.sub("/","\\/",lfw_ds_dir)

                
                if best_weights == "":
                    lm = "1.0"
                    wp = str(lfw)
                    ds = str(dsw)
                else:
                    lm, wp, ds = best_weights.split("|")
                    lfw_ds_dir = home_dir+"lfw_ds_"+str(wp)+"_"+str(ds)
                    lfw_ds_cdir=re.sub("/","\\/",lfw_ds_dir)
                print lm, wp, ds
#                process = subprocess.Popen("ssh hpc \"mkdir %s; \
#                cp %s %s; \
#                sed -i 's/LFW=[-+]\?[0-9]*\.\?[0-9]*/LFW=%s/' %s; \
#                sed -i 's/DS=[-+]\?[0-9]*\.\?[0-9]*/DS=%s/' %s; \
#                sed -i 's/EXP_DIR=.*/EXP_DIR=%s/' %s; \
#                nohup %s %s\""\
#                %(lfw_ds_dir,config_file,lfw_ds_dir,\
#                  lfw,lfw_ds_dir+"/e2e.config",\
#                  ds,lfw_ds_dir+"/e2e.config",\
#                  lfw_ds_cdir,lfw_ds_dir+"/e2e.config",\
#                  pipeline,lfw_ds_dir+"/e2e.config"), 
#                                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)   

                if dev_test == "train":
                    process = subprocess.Popen("""ssh hpc "mkdir %s; cp %s %s; \
                    sed -i 's/EXP_DIR=.*/EXP_DIR=%s/' %s; 
                    sed -i 's/RAW_INPUT=.*/RAW_INPUT=\$DATA_DIR\/wsj100\-sent\-20120712\/%s_20120712.50.txt/' %s; 
                    sed -i 's/REF=.*/REF=\$DATA_DIR\/wsj100\-sent\-20120712\/%s_20120712_reference.50.txt/' %s; \
                    echo %s | awk '{print \\\"LanguageModel\\\",\$1\\\"\\nWordPenalty\\\",\$2\\\"\\nDerivSize\\\",\$3}'>%s; \
                    KBEST_CDEC=%s TUNE_KBEST_FILE=%s OUT_CDEC_ONEBEST=%s WEIGHT_FILE=%s %s %s" """\
                                               %(lfw_ds_dir,config_file,lfw_ds_dir,lfw_ds_cdir,lfw_ds_dir+"/e2e.config",dev_test,lfw_ds_dir+"/e2e.config",dev_test,lfw_ds_dir+"/e2e.config",\
                                                 " ".join([lm,wp,ds]),lfw_ds_dir+"/"+weight_file,\
                                                 nbest,lfw_ds_dir+"/"+tune_nbest,lfw_ds_dir+"/"+one_best,lfw_ds_dir+"/"+weight_file,pipeline,lfw_ds_dir+"/e2e.config"), 
                                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) 
                else:
                    process = subprocess.Popen("""ssh hpc "mkdir %s; cp %s %s; \
                    sed -i 's/EXP_DIR=.*/EXP_DIR=%s/' %s; 
                    sed -i 's/RAW_INPUT=.*/RAW_INPUT=\$DATA_DIR\/wsj100\-sent\-20120712\/%s_20120712.txt/' %s; 
                    sed -i 's/REF=.*/REF=\$DATA_DIR\/wsj100\-sent\-20120712\/%s_20120712_reference.txt/' %s; \
                    echo %s | awk '{print \\\"LanguageModel\\\",\$1\\\"\\nWordPenalty\\\",\$2\\\"\\nDerivSize\\\",\$3}'>%s; \
                    KBEST_CDEC=%s TUNE_KBEST_FILE=%s OUT_CDEC_ONEBEST=%s WEIGHT_FILE=%s %s %s" """\
                                               %(lfw_ds_dir,config_file,lfw_ds_dir,lfw_ds_cdir,lfw_ds_dir+"/e2e.config",dev_test,lfw_ds_dir+"/e2e.config",dev_test,lfw_ds_dir+"/e2e.config",\
                                                 " ".join([lm,wp,ds]),lfw_ds_dir+"/"+weight_file,\
                                                 nbest,lfw_ds_dir+"/"+tune_nbest,lfw_ds_dir+"/"+one_best,lfw_ds_dir+"/"+weight_file,pipeline,lfw_ds_dir+"/e2e.config"), 
                                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)    


                process.communicate()    
                if best_weights != "":
                    break            
            if best_weights != "":
                break
    

    def getGridData(self,code_dir):
        print "ssh hpc \"cd %s; head lfw_ds_*/*bleu*\""%code_dir
        process = subprocess.Popen("ssh hpc \"cd %s; head lfw_ds_*/*bleu*\""%code_dir,
                                   shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)     
        a = process.communicate()[0]
        feat_dict = defaultdict()
        print type(a), len(a.split("\n\n"))
        for i in map(lambda x:x.strip(), a.split("\n\n")):
            
            feat_str, bleu_str = i.split("\n")
            feats =  re.search("([a-zA-Z_]+)_([-+0-9_]+)",feat_str).group(1)
            feat_values =  re.search("([a-zA-Z_]+)_([-+0-9_]+)",feat_str).group(2)
            
            bleu = float(re.search("BLEU = ([-+]?[0-9]*\.?[0-9]*)",bleu_str).group(1))
            bp = float(re.search("BP=([-+]?[0-9]*\.?[0-9]*)",bleu_str).group(1))
            feat_dict[feat_values] = (bleu,bp)
        lfw_list = []
        ds_list = []
        bleu_list = []
        
        for k in feat_dict:
            
            l,d=k.split("_")
            
            lfw_list.append(int(l))
            ds_list.append(int(d))
            bleu_list.append(feat_dict[k][0])
            
           # print k,feat_dict[k]

        for key, value in sorted(feat_dict.iteritems(), key=lambda (k,(bleu,bp)): (bleu,k), reverse=True):
            print " , ".join(key.split("_")), ",",value[0]
            
            
        return lfw_list,ds_list, bleu_list
    
    def getData(self,code_dir,data_type):

        

        if data_type == "linesearch":
            print "ssh hpc \"cd %s; find . | egrep '/lfw[-]?[0-9]+' | egrep '*bleu*' | xargs head \""%code_dir
            process = subprocess.Popen("ssh hpc \"cd %s; find . | egrep '/lfw[-]?[0-9]+' | egrep '*bleu*' | xargs head \""%code_dir,
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)    
        elif data_type == "rerank":
            print "ssh hpc \"cd %s; find . | egrep 'mertlfw[-]?[0-9]+_[-]?[0-9]+' | egrep '*bleu*' | xargs head \""%code_dir
            process = subprocess.Popen("ssh hpc \"cd %s; find . | egrep '/mertlfw[-]?[0-9]+_[-]?[0-9]+' | egrep '*bleu*' | xargs head \""%code_dir,
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)                


#        process = subprocess.Popen("ssh hpc \"cd %s; find . | egrep 'mertlfw\-3_[-]?[0-9]+' | egrep '*bleu*' | xargs head \""%code_dir,
#                                   shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)    

        a = process.communicate()[0]

        lfw_dict = defaultdict()
        for i in map(lambda x:x.strip(), a.split("\n\n")):
            
            lfw_str, bleu_str = i.split("\n")
            if data_type == "linesearch":
                lfw = int(re.search("lfw([-+]?[0-9]*\.?[0-9]*)",lfw_str).group(1))
            elif data_type == "rerank":
                lfw =  int(re.search("mertlfw\-3_([-+]?[0-9]*\.?[0-9]*)",lfw_str).group(1))
            
            bleu = float(re.search("BLEU = ([-+]?[0-9]*\.?[0-9]*)",bleu_str).group(1))
            bp = float(re.search("BP=([-+]?[0-9]*\.?[0-9]*)",bleu_str).group(1))
            lfw_dict[lfw] = (bleu,bp)
        
        lfw_list = []
        bleu_list = []
        bp_list = []
        for k in sorted(lfw_dict.iterkeys()):
            lfw_list.append(k)
            bleu_list.append(lfw_dict[k][0])
            bp_list.append(lfw_dict[k][1])
            print k,lfw_dict[k]


        return lfw_list, bp_list,bleu_list
        
        
    def drawFigure(self,base_dir,tuning_method):
        test_dir = base_dir+"/"+"test"
        dev_dir = base_dir+"/"+"dev"
        train_dir = base_dir+"/"+"train"
        
        if tuning_method == "linesearch":
            train_lfw_list,train_bp_list,train_bleu_list = self.getData(train_dir,"linesearch")
            train_mert_list,train_mert_bp_list,train_mert_bleu_list = self.getData(train_dir,"rerank")
#            test_lfw_list,test_bp_list,test_bleu_list = self.getData(test_dir,"linesearch")
#            dev_lfw_list,dev_bp_list,dev_bleu_list = self.getData(dev_dir,"linesearch")
#            oneplot('length feature weight','bleu score',train_lfw_list,  train_bleu_list)
#            oneplot('length feature weight','bleu score',train_mert_list,  train_mert_bleu_list)
            scatterplot('length feature weight','bleu score',train_lfw_list,  train_bleu_list,  train_mert_list,  train_mert_bleu_list)
            scatterplot('length feature weight','brevity penalty',train_lfw_list,  train_bp_list,  train_mert_list,train_mert_bp_list)
#            scatterplot('length feature weight','brevity penalty',dev_lfw_list,  dev_bp_list,  test_lfw_list,test_bp_list)
#            scatterplot('length feature weight','bleu score',dev_lfw_list,  dev_bleu_list,  test_lfw_list,test_bleu_list)
        elif tuning_method == "gridsearch":
            train_lfw_list,train_ds_list,train_bleu_list = self.getGridData(train_dir)
#            dev_lfw_list,dev_ds_list,dev_bleu_list = self.getGridData(dev_dir)
#            tes_lfw_list,tes_ds_list,test_bleu_list = self.getGridData(test_dir)
            draw3d(train_lfw_list,train_ds_list,train_bleu_list)
#            draw3d(dev_lfw_list,dev_ds_list,dev_bleu_list)
#            draw3d(tes_lfw_list,tes_ds_list,test_bleu_list)
        


#        oneplot('length feature weight','bleu score',dev_lfw_list,  dev_bleu_list)


def draw3d(dev_lfw_list,dev_ds_list,dev_bleu_list):


    

    mpl.rcParams['legend.fontsize'] = 10
    
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot(dev_lfw_list,dev_ds_list,dev_bleu_list,"o", label='dev set')

    ax.set_xlabel('length feature weight')
    ax.set_ylabel('derivation size weight')
    ax.set_zlabel('bleu score')
    ax.legend()
    
    plt.show()
    
def oneplot(x_lable,y_label,x1,y1):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(x1, y1, 'o-')
    ax.grid("on")
    xlabel(x_lable)
    ylabel(y_label)
    plt.show()
    
def scatterplot(x_label, y_label, x1,y1, x2,y2):
#    ax = plt.subplot(111)two
#    ax.scatter(x, y)
#    grid('on')

#    fig = plt.figure()
#    ax = fig.add_subplot(111)To reduce variance it is best to use as much data as possible at each stage
    

#    ax.plot(x1, y1, 'o-',x2,y2,'*-')
#    ax.grid("on")

    text_x = x1[-3]*4/float(7)
    text_y = 3*max([max(y1),max(y2)])/float(4)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.text(text_x, text_y, '0-train;*-train rerank')
    plt.plot(x1, y1, 'o-',x2,y2,'*-')
    plt.grid("on")
    plt.show()

#    (k, b,z) = polyfit(x,y,2)
#    print 'k:', k, '\tbias:', b
#    yp = polyval([k,b,z],x)
#    plot(x,yp)
#    xlabel(x_label)
#    ylabel(y_label)
#    title('linear regression fit: y = {0}*x*x + {1}*x + {2}'.format(k,b,z))
#    savefig('plot.pdf')
#    show()
            
class frame(object):
    def __init__(self):
        '''
        Constructor
        '''
    
    def generateFrameRules(self,frame_file,frame_output):
        output_file = open(frame_output, "w")
        output_file_info = open(frame_output+".info.txt", "w")
        file_names = os.listdir(frame_file)
        for a_file in file_names:
            
            #print a_file
            if not re.search("xml$",a_file):
                continue
            a_xml_tree = parse(frame_file+"/"+a_file)
            for elem in a_xml_tree.getiterator("roleset"):
                #print "current verb sense is ",elem.get("id")
                for eg in elem.getiterator("example"):
                    pre_str  = ""
                    args_list = []
                    arg_var_dict = defaultdict()
                    rhs = []
                    output_str = ""
                    output_rule = ""
                    for child in list(eg):
                        if child.tag == "text":
                            #print child.text
                            output_file_info.write("#"+" ".join(child.text.strip().split())+"\n")
                            
                        if child.tag == "arg":
                            if not re.match("[0-9]+",child.get("n")):
                                print a_file,child.get("n"),child.keys()
                                if child.get("f")!=None:
                                    
                                    print "==========================unknown f attribute",a_file,child.get("f")
                                raw_input("press enter to continue")
                                continue
                            for a in child.keys():
                                if a not in ["n","f"]:
                                    print "++++++++++++++++++++++++unseen attribute", a_file,a,child.get(a)
                            if child.get("f") != None:
                                if child.get("f").isupper():
                                    #print "==========================unknown f attribute",a_file,child.get("f")
                                    pass
                                else:
                                    output_str += child.get("f")+" "
                                    rhs.extend(child.get("f").strip().strip("(").strip(")").split())
                                    
                            output_str += "ARG"+child.get("n")+" "
                            args_list.append("ARG"+child.get("n"))
                            rhs.append("ARG"+child.get("n"))
                            
                        if child.tag == "rel":
                            pre_str = re.sub("\.","-",elem.get("id"))
                            output_str += elem.get("id") +" "
                            rhs.append(pre_str)
                            
                    if len(rhs) == 0 or pre_str == "":
                        continue
                    
                    output_rule += "q.(/ "+pre_str
                    args_list.sort()
                    for i, a in enumerate(args_list):
                        output_rule += " :"+a+" x"+str(i)
                        arg_var_dict[a]="x"+str(i)
                    output_rule += ") -> S("
                    for i, a in enumerate(rhs):
                        if a in arg_var_dict:
                            output_rule += "qnp."+arg_var_dict[a]+" "
                        elif re.search("\-",a):
                            #output_rule += "q."+a+" "
                            a=re.sub("\-[0-9]+$","",a)
                            output_rule += "VB("+a+") " 
                        else:
                            output_rule += "IN("+a+") "
                    output_rule = output_rule.strip()
                    output_rule +=")"

                    output_file.write(output_rule+"\n")
                    output_file_info.write(output_str+"\n")
                    output_file_info.write(output_rule+"\n\n")
        output_file.close()
        output_file_info.close()
        
class amrUtil(object):
    def print_amr(self,amr_node,inden):
        out_str = ""
        if amr_node.feats:
            if inden != 0:
                temp = " (" + amr_node.val
            else:
                temp = "(" + amr_node.val
        else:
            temp = " "+amr_node.val
        out_str += temp
        inden += len(temp)
        if amr_node.feats:
            '''
            if current node is a sub amr
            '''
            instance_id = 0
            for i, a_edge in enumerate(amr_node.feats):
                if re.match("/",a_edge.edge):
                    instance_id = i
                    break
            for i, a_edge in enumerate(amr_node.feats):
                if i == instance_id:
                    out_str += " "+a_edge.edge+" "+a_edge.node.val
                    if i < len(amr_node.feats) -1:
                        out_str += "\n"
                else:
                    out_str += inden*" "+a_edge.edge +self.print_amr(a_edge.node,inden+len(a_edge.edge))
                    if i < len(amr_node.feats) -1:
                        out_str += "\n"
        if amr_node.feats:
            out_str+=")"
        return out_str
                                        
            
        

class quantity(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
    def getMonetaryQuant(self,amr_feat_graph):
        temp_rule = []
        if amr_feat_graph.feats and "monetary-quantity" in map(lambda x:x.node.val, amr_feat_graph.feats):
            temp_rule.append(self.generateTempRule(amr_feat_graph))
        for a_edge in amr_feat_graph.feats:
            temp_rule.extend(self.getMonetaryQuant(a_edge.node))
        return temp_rule
  
            
    def generateTempRule(self,amr_feat_graph):
        for a_edge in amr_feat_graph.feats:
            if a_edge.edge == ":quant":
                cd = a_edge.node.val
                if len(cd) < 7:
                    return "qcd."+cd+" -> NP(CD("+self.insertComma(cd,3)+"))"
                elif 7<= len(cd) < 10:
                    new_cd = self.insertPoint(cd,6)
                    return "qcd."+cd+" -> NP(CD("+new_cd+") NN(million))"
                elif 13 > len(cd) >= 10:
                    new_cd = self.insertPoint(cd,9)
                    return "qcd."+cd+" -> NP(CD("+new_cd+") NN(billion))"
                elif 13 <= len(cd):
                    new_cd = self.insertPoint(cd,12)
                    return "qcd."+cd+" -> NP(CD("+new_cd+") NN(trillion))"   
                    
    def insertPoint(self,cd,point_loc):
        new_cd = re.sub("\.?0+$","",cd[:-point_loc] +"."+cd[-point_loc:])
        return new_cd
    
    def insertComma(self,cd,comma_loc):
        if re.search("\.",cd):
            return cd
        if comma_loc >= len(cd):
            return cd
        return cd[:-comma_loc] +","+cd[-comma_loc:]
    
def main(amr_file,output):
    # input files: .amr
    f_in = open(amr_file)

    inputs = get_input(f_in.read())

    '''
    start of quantity rules
    '''
    amr_sr = quantity()
    temp_rule_file = open(output,"w")
    for amr_fg in inputs:
        temp_rules = amr_sr.getMonetaryQuant(amr_fg)
        for t in temp_rules:
            temp_rule_file.write(t+"\n")
    temp_rule_file.close()
        
    #raw_input("Press Enter to continue")
    '''
    end of quantity rules
    '''
def morph(morph_file,output):
    mph = morphology()
    mph.generateMorphRules(morph_file,output)

def frame_main(frame_file,frame_output):
    fm = frame()
    fm.generateFrameRules(frame_file, frame_output)
    
def print_amr(amr_file,output_file):
    '''
    print out amr in a pretty format
    '''
    print output_file
    output = open(output_file,"w")
    f_in = open(amr_file)
    inputs = get_input(f_in.read())
    au = amrUtil()
    for amr_fg in inputs:
        output.write(au.print_amr(amr_fg, 0)+"\n")
        output.write("\n")
    output.close()

def truning_main(dev_test,base_dir,pipeline_dir,tuning_method,draw,optimized_weights):
    tn = Tuning()
#    if tuning_method == "linesearch":
#        tn.lineSearch(dev_test,base_dir,pipeline_dir,optimized_weights)
#    elif tuning_method == "gridsearch":
#        tn.gridSearch(dev_test,base_dir,pipeline_dir,optimized_weights)
#    elif tuning_method == "mertexc":
#        tn.MERTexc(-3,dev_test,base_dir)

    if draw:
        tn.drawFigure(base_dir,tuning_method)
        
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-q", "--quantity",
                      dest="quant", action="store_true",
                      help="generate temporary quantity rules")
    parser.add_option("-a", "--amr",
                      dest="amr_input",
                      help="input amrs")
    parser.add_option("-o", "--output",
                      dest="output",
                      help="output temporary quantity rules to a file")   

    parser.add_option("-m", "--morphology",
                      dest="morph", action="store_true",
                      help="generate morphology rules")  
    parser.add_option("-p", "--morph",
                      dest="morph_input",
                      help="input morphology file")    
    parser.add_option("-w", "--outputmorph",
                      dest="morph_output",
                      help="output morphology rules to a file")  
    
    parser.add_option("-f", "--frame",
                      dest="frame", action="store_true",
                      help="generate frame rules")  
    parser.add_option("--frame_file",
                      dest="frame_file",
                      help="input frame files")    
    parser.add_option("--frame_output",
                      dest="frame_output",
                      help="output frame rules to a file")  
    
    parser.add_option("--pprint",
                      dest="pprint",action="store_true",
                      help="pprint amrs")
    parser.add_option("--ppamr",
                      dest="ppamr",
                      help="output pretty amr to a file")
    
    parser.add_option("--tuning",
                      dest="tuning",action="store_true",
                      help="tuning feature weights")
    parser.add_option("--tuning_method",
                      dest="tuning_method",
                      help="tuning methods: l(line search);g(grid search);m(mert)")
    parser.add_option("--dev_test",
                      dest="dev_test",
                      help="tune on dev or test data set")
    parser.add_option("--base_dir",
                      dest="base_dir",
                      help="my experiment directory")
    parser.add_option("--pipeline_dir",
                      dest="pipeline_dir",
                      help="pipeline directory")
    parser.add_option("--optimized_weights",
                      dest="optimized_weights",default="",
                      help="optimized weights")    
    parser.add_option("--draw",
                      dest="draw",action="store_true",
                      help="draw figures")
    
    
    (options, args) = parser.parse_args()
    if options.quant:
        main(options.amr_input,options.output)
    if options.morph:
        morph(options.morph_input, options.morph_output)
    if options.frame:
        frame_main(options.frame_file,options.frame_output)
    
    if options.pprint:
        print_amr(options.amr_input,options.ppamr)      
    if options.tuning:
        truning_main(options.dev_test,options.base_dir,options.pipeline_dir,options.tuning_method,options.draw,options.optimized_weights)
               
        
        
            
    
        