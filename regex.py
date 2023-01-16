import re

#no longer support, use for temporaly test.
if __name__ == "__main__":
    st = ['CH9340_SBR_100G//SNK_2(1-13)_TO_RBR0003_2(1-16)//(SNK-RBR0003)','CH9380_SBR_100G//SNK_2(2-15)_TO_PKN0001_2(1-16)//(SNK-PKN0001)','CH9540_SBR_100G//CPN0012_2(1-16)_TO_SNI_2(1-16)//(CPN0012-SNI)']
    for sub_st in st:
        _regex = re.findall(r'([\w-]+\//)+([\w-]+)+(\W\d\W\d*\W)+([\w-]+TO+[\w-])+([\w-]+)',sub_st)
        print("src: ", _regex[0][1])
        print("dst: ", _regex[0][4])