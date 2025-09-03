25.9.2
进行集成测试，但仍存在一定问题：
1）create_transaction函数中返回的数据结构为：
        result = {
            "main_transaction": main_transaction,
            "change_transaction": change_transaction,
            "selected_values": selected_values,
            "change_value": change_value,
            "total_amount": sum(v.value_num for v in selected_values),
            "transaction_fee": 0  # Fee calculation can be added here
        }
    其中"total_amount"可能有误，其原目的应是记录主交易（即，main tx，非change tx）的金额，这里是遍历并sum所有被选值的金额（value值）。
2）CreatSingleTransaction.py及其集成和单元测试中的Value貌似没有使用AccValue（链式集成Values），只是使用了最原始的Value类。

25.9.3
1）test_integration_creat_single_transaction.py测试中test_real_multiple_value_selection的检测逻辑错误，其将total_selected = sum(v.value_num for v in selected_values)，selected_values已经是被分割后的值，因此total_selected恒等于500，后续检测逻辑并未意识到selected_values已经是被分割后的值。
2）test_integration_creat_single_transaction.py测试中还存在其他错误。
